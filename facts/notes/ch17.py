"""Chapter 17's instructor notes (financial statements for a lender, a Part V capstone case): the values each note
states, and the claims its wording makes.

The case is set in July of d.N. The staff accountant prepares statements for fiscal d.C with d.P as the comparative
year, so the three year-ends of the window are d.F, d.P, and d.C, and "1 January" of the comparative year is the start
of d.P. Trial balances follow Requirement 1 (postings on or before the as-of date, a year-end close left out only when
it is dated on the as-of date), and flows leave the closes out. Amounts are rounded half away from zero.

The adjustments are the ones the notes prescribe: A1 the payroll of each year's last days paid in the next fiscal year,
by working day (the registers of the pay periods that end in the year and are paid in the next, plus the share of the
period that crosses the year-end; where those periods have no registers, as at the end of d.C, the cost per working day
of the last eight processed periods); A2 revenue cutoff by delivery date (invoices posted in a later year than the
deliveries they bill, and shipment lines never invoiced, at order price less discount); A3 the accruals still open at a
year-end that are older than the longest clearing lag of any invoiced accrual; A4 the interest each note has accrued at
the year-end, from its schedule.

The passed items P1 (the allowance) and P2 (expected returns) are estimates: r5 gives each at the d.C year-end and its
effect on d.C income net of the same estimate at the end of d.P, which would reverse in d.C.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache

from notes import note
from notes.case3 import burden, completions, depreciation as plant_depreciation, processed, rate, working_days, yearly
from notes.case4 import capital_invoices, disposals, flow, ledger, materials_issues, opening_entry, restated, xr
from notes.ch08 import BUCKETS, abbreviated, bucket_of, open_invoices
from notes.ch12 import invoices_by_delivery, late_december_cost

CHAPTER = "chapters/17-statements-for-a-lender/chapter.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
MATERIALITY = 0.05      # the controller's materiality: 5% of income before income taxes as the ledger records it
FEDERAL = 0.21          # the federal rate the memo applies to a C corporation
TRIVIAL = 0.05          # clearly trivial, as a share of materiality
WRITE_DOWN = ("Damaged", "Quality Concern")     # the return reasons of passed item P3
# The never-posted accounts the note names, because each leads to a later requirement or a matter for the CFO.
NAMED = {"1030", "1140", "2070", "2080", "2120", "3040", "6170", "7010"}
LEADS = ["2080", "2120", "1140", "1030", "7010"]
# Property and equipment: each cost account with its accumulated depreciation account, and the note's class names.
PAIRS = [("1110", "1150"), ("1120", "1160"), ("1130", "1170"), ("1185", "1186")]
CLASSES = {"1150": "furniture and fixtures", "1160": "warehouse", "1170": "office", "1186": "manufacturing"}
GROUP_ORDER = ["Furniture", "Lighting", "Textiles", "Accessories"]     # the product lines in the book's order
# The balance-sheet groups of the adjusted statements (account numbers of the chart).
CASH, RECEIVABLES, INVENTORIES, PREPAID = ["1010"], ["1020", "1030"], ["1040", "1045", "1046", "1090"], ["1050"]
PAYABLES, PAYROLL, COMMISSIONS, ACCRUED, SALES_TAX, CREDITS = (["2010"], ["2030", "2031", "2032", "2033"], ["2034"],
                                                               ["2040"], ["2050"], ["2060"])


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def ye(year: int) -> str:
    return f"{year}-12-31"


def day_month(day: str) -> str:
    """'2027-02-23' -> '23 February'."""
    return f"{int(day[8:10])} {MONTHS[int(day[5:7]) - 1]}"


def month_of(day: str) -> str:
    return MONTHS[int(day[5:7]) - 1]


def days(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def first_weekday(day: str) -> str:
    """The first Monday-to-Friday date of a date's month."""
    first = date.fromisoformat(day[:8] + "01")
    while first.weekday() >= 5:
        first += timedelta(days=1)
    return first.isoformat()


def month_before(day: str) -> str:
    """'2026-12-01' -> '2026-11'."""
    y, m = int(day[:4]), int(day[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def entry(*lines) -> list[tuple[str, str, float]]:
    """A journal entry's lines from (account, debits less credits): ("Dr" or "Cr", account, amount), debits first, each
    side in the order given, zero lines left out."""
    return ([("Dr", a, xr(v)) for a, v in lines if v > 0.004] + [("Cr", a, xr(-v)) for a, v in lines if v < -0.004])


def short_series(dates: list[str]) -> str:
    """'2027-01-01, 01-04, 02-01': the first date in full, the others without their year."""
    return ", ".join(x if i == 0 else x[5:] for i, x in enumerate(dates))


# --- the chart and the ledger ----------------------------------------------------------------------

@lru_cache(maxsize=None)
def chart(d) -> dict[str, dict]:
    return {str(n): dict(id=i, name=nm, type=t, sub=s, normal=nb, active=a) for n, i, nm, t, s, nb, a in d.q(
        "SELECT AccountNumber, AccountID, AccountName, AccountType, AccountSubType, NormalBalance, IsActive FROM Account")}


def accounts_of(d, *subs) -> list[str]:
    return [n for n, a in chart(d).items() if a["sub"] in subs]


def pl_accounts(d) -> list[str]:
    return [n for n, a in chart(d).items() if a["type"] in ("Revenue", "Expense") and a["sub"] != "Header"]


@lru_cache(maxsize=None)
def tb(d, asof: str) -> dict[str, float]:
    """Requirement 1's trial balance (debits less credits) of the accounts with postings at the as-of date."""
    out = {}
    for n, rows in ledger(d).items():
        live = [dr - cr for src, day, close, op, dr, cr, k in rows if day <= asof and not (close and day == asof)]
        if live:
            out[n] = sum(live)
    return out


def bal(d, nums, asof: str) -> float:
    t = tb(d, asof)
    return sum(t.get(n, 0.0) for n in nums)


def activity(d, nums, year: int) -> float:
    """Debits less credits posted in a fiscal year, the closes left out."""
    dr, cr = flow(d, nums, f"{year}-01-01", ye(year))
    return dr - cr


@lru_cache(maxsize=None)
def net_income(d, year: int) -> float:
    return xr(-activity(d, pl_accounts(d), year))


def materiality(d, year: int) -> float:
    return xr(net_income(d, year) * MATERIALITY)


@lru_cache(maxsize=None)
def income(d, year: int) -> dict:
    """The recorded income statement of a fiscal year, by AccountSubType."""
    def sub(*subs):
        return activity(d, [n for n in pl_accounts(d) if chart(d)[n]["sub"] in subs], year)
    out = dict(opr=-sub("Operating Revenue"), ret=sub("Contra Revenue"), cogs=sub("COGS"), opx=sub("Operating Expense"),
               intr=sub("Other Expense"), loss=activity(d, ["7020"], year))
    out = {k: xr(v) for k, v in out.items()}
    out.update(net_rev=xr(out["opr"] - out["ret"]), gm=xr(out["opr"] - out["ret"] - out["cogs"]),
               op=xr(out["opr"] - out["ret"] - out["cogs"] - out["opx"]))
    out["ni"] = xr(out["op"] - out["intr"] - out["loss"])
    return out


@lru_cache(maxsize=None)
def recorded(d, year: int) -> dict:
    """The recorded balance sheet at a year-end."""
    t = tb(d, ye(year))
    sub = lambda *subs: sum(v for k, v in t.items() if chart(d)[k]["sub"] in subs)
    return dict(n=len(t), zero=sum(1 for v in t.values() if abs(v) < 0.005),
                debits=xr(sum(v for v in t.values() if v > 0)), credits=xr(-sum(v for v in t.values() if v < 0)),
                ta=xr(sub("Current Asset", "Contra Current Asset", "Fixed Asset", "Contra Fixed Asset", "Noncurrent Asset")),
                ca=xr(sub("Current Asset", "Contra Current Asset")), cl=xr(-sub("Current Liability")),
                notes=xr(-t.get("2110", 0.0)), re=xr(-t.get("3030", 0.0)), stock=xr(-t.get("3010", 0.0)))


@lru_cache(maxsize=None)
def never_posted(d) -> list[tuple]:
    return [(str(n), nm, a) for n, nm, a in d.q(
        "SELECT a.AccountNumber, a.AccountName, a.IsActive FROM Account a WHERE a.AccountSubType <> 'Header' "
        "AND NOT EXISTS (SELECT 1 FROM GLEntry g WHERE g.AccountID = a.AccountID) ORDER BY 1")]


def opening_line(d, number: str) -> float:
    """The opening entry's line to an account, credits less debits for a credit balance and debits less credits else."""
    v = d.one("SELECT COALESCE(SUM(Debit) - SUM(Credit), 0) FROM GLEntry WHERE AccountID = ? AND VoucherNumber = ?",
              d.account(number), opening_entry(d))
    return xr(-v if chart(d)[number]["normal"] == "Credit" else v)


def no_tax_account(d) -> bool:
    return d.one("SELECT COUNT(*) FROM Account WHERE AccountName LIKE '%Income Tax%'") == 0


# --- Requirement 3: accrued expenses ------------------------------------------------------------------

@lru_cache(maxsize=None)
def accruals(d) -> dict:
    """The Accrual entries with what cleared them: invoice lines (their debits to 2040) and Accrual Adjustment entries."""
    a2040 = d.account("2040")
    # each entry's lines: debits to an expense account, credits to 2040, and any other line
    acc = {jid: dict(id=jid, number=n, date=dt, amount=amt, account=str(acct), debits=nd, credits=nc, other=no, clear=[])
           for jid, n, dt, amt, acct, nd, nc, no in d.q(
               "SELECT j.JournalEntryID, j.EntryNumber, j.PostingDate, SUM(CASE WHEN g.AccountID = ?1 THEN g.Credit ELSE 0 END), "
               "MAX(CASE WHEN g.Debit > 0 THEN a.AccountNumber END), SUM(g.Debit > 0 AND a.AccountType = 'Expense'), "
               "SUM(g.Credit > 0 AND g.AccountID = ?1), SUM(NOT ((g.Debit > 0 AND a.AccountType = 'Expense') "
               "OR (g.Credit > 0 AND g.AccountID = ?1))) FROM JournalEntry j JOIN GLEntry g ON g.SourceDocumentType = "
               "'JournalEntry' AND g.SourceDocumentID = j.JournalEntryID JOIN Account a ON a.AccountID = g.AccountID "
               "WHERE j.EntryType = 'Accrual' GROUP BY 1", a2040)}
    lines = d.q("SELECT l.AccrualJournalEntryID, g.PostingDate, g.Debit, l.PILineID, pi.InvoiceNumber FROM PurchaseInvoiceLine l "
                "JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = l.PurchaseInvoiceID JOIN GLEntry g ON g.SourceDocumentType = "
                "'PurchaseInvoice' AND g.SourceLineID = l.PILineID AND g.AccountID = ? WHERE l.AccrualJournalEntryID IS NOT NULL",
                a2040)
    for jid, day, amount, line, number in lines:
        if jid in acc:
            acc[jid]["clear"].append(dict(date=day, amount=amount, kind="invoice", doc=number))
    adjusted = d.q("SELECT j.ReversesJournalEntryID, j.PostingDate, SUM(g.Debit), j.EntryNumber, j.Description FROM JournalEntry j "
                   "JOIN GLEntry g ON g.SourceDocumentType = 'JournalEntry' AND g.SourceDocumentID = j.JournalEntryID "
                   "AND g.AccountID = ? WHERE j.EntryType = 'Accrual Adjustment' GROUP BY j.JournalEntryID", a2040)
    for jid, day, amount, number, text in adjusted:
        if jid in acc:
            acc[jid]["clear"].append(dict(date=day, amount=amount, kind="adjustment", doc=number, text=text or ""))
    lags = sorted(days(a["date"], min(c["date"] for c in a["clear"] if c["kind"] == "invoice"))
                  for a in acc.values() if any(c["kind"] == "invoice" for c in a["clear"]))
    return dict(entries=acc, lines=lines, adjustments=adjusted, lags=lags, window=lags[-1])


def open_amount(a: dict, asof: str) -> float:
    return xr(a["amount"] - sum(c["amount"] for c in a["clear"] if c["date"] <= asof))


def invoiced(a: dict) -> bool:
    return any(c["kind"] == "invoice" for c in a["clear"])


@lru_cache(maxsize=None)
def composition(d, year: int) -> dict:
    """Account 2040 at a year-end: the opening line, freight not yet settled, and the open accruals by age."""
    asof, a2040 = ye(year), d.account("2040")
    acc = accruals(d)
    young, old = [], []
    for a in acc["entries"].values():
        if a["date"] > asof:
            continue
        amount = open_amount(a, asof)
        if amount <= 0.004:
            continue
        item = dict(a, open=amount, age=days(a["date"], asof))
        (old if item["age"] > acc["window"] else young).append(item)
    shipped = d.one("SELECT COALESCE(SUM(Credit), 0) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'Shipment' "
                    "AND PostingDate <= ?", a2040, asof)
    december = d.one("SELECT COALESCE(SUM(Credit), 0) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'Shipment' "
                     "AND PostingDate BETWEEN ? AND ?", a2040, f"{year}-12-01", asof)
    settled = d.one("SELECT COALESCE(SUM(g.Debit), 0) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
                    "AND g.SourceDocumentType = 'JournalEntry' WHERE g.AccountID = ? AND j.EntryType = 'Freight Settlement' "
                    "AND g.PostingDate <= ?", a2040, asof)
    freight = xr(shipped - settled)
    opening = opening_line(d, "2040")
    out = dict(opening=opening, freight=freight, december=xr(december), excess=xr(freight - december),
               young=xr(sum(i["open"] for i in young)), old=xr(sum(i["open"] for i in old)), n_old=len(old),
               old_items=old, young_items=young, ledger=xr(-bal(d, ["2040"], asof)))
    out["total"] = xr(opening + freight + out["young"] + out["old"])
    return out


def stale(d, year: int) -> float:
    return composition(d, year)["old"]


# --- Requirement 4: cutoff ------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def revenue_accounts(d) -> dict[str, str]:
    """Each item group's revenue account, from the ledger's invoice postings."""
    rows = d.q("SELECT i.ItemGroup, a.AccountNumber FROM GLEntry g JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = "
               "g.SourceLineID JOIN Item i ON i.ItemID = sil.ItemID JOIN Account a ON a.AccountID = g.AccountID "
               "WHERE g.SourceDocumentType = 'SalesInvoice' AND a.AccountSubType = 'Operating Revenue' GROUP BY 1, 2")
    return {g: str(a) for g, a in rows}


@lru_cache(maxsize=None)
def freight_account(d) -> list[str]:
    """The revenue accounts the invoices credit with no invoice line (the freight billed)."""
    return [str(r[0]) for r in d.q("SELECT DISTINCT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                                   "WHERE g.SourceDocumentType = 'SalesInvoice' AND a.AccountSubType = 'Operating Revenue' "
                                   "AND g.SourceLineID IS NULL")]


def ordered_groups(groups) -> list[str]:
    return [g for g in GROUP_ORDER if g in groups] + sorted(g for g in groups if g not in GROUP_ORDER)


@lru_cache(maxsize=None)
def late(d) -> list[dict]:
    """Invoices posted in another year than the latest delivery of the goods they bill, with their segment, groups,
    tax, and freight."""
    out = []
    for i in invoices_by_delivery(d):
        if not i["late"]:
            continue
        segment, tax, freight = d.q("SELECT c.CustomerSegment, si.TaxAmount, si.FreightAmount FROM SalesInvoice si JOIN Customer c "
                                    "ON c.CustomerID = si.CustomerID WHERE si.SalesInvoiceID = ?", i["id"])[0]
        groups = dict(d.q("SELECT it.ItemGroup, SUM(sil.LineTotal) FROM SalesInvoiceLine sil JOIN Item it ON it.ItemID = sil.ItemID "
                          "WHERE sil.SalesInvoiceID = ? GROUP BY 1", i["id"]))
        out.append(dict(i, year=int(i["delivered"][:4]), segment=segment, tax=tax, freight=freight, groups=groups))
    return out


@lru_cache(maxsize=None)
def unbilled(d) -> list[dict]:
    """Shipment lines never invoiced, at order price less discount."""
    return [dict(id=k, shipped=s, delivered=dl, value=v, std=c, group=g, segment=seg) for k, s, dl, v, c, g, seg in d.q(
        "SELECT sl.ShipmentLineID, s.ShipmentDate, s.DeliveryDate, ROUND(sl.QuantityShipped * sol.UnitPrice * (1 - sol.Discount), 2), "
        "sl.ExtendedStandardCost, i.ItemGroup, c.CustomerSegment FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
        "JOIN SalesOrderLine sol ON sol.SalesOrderLineID = sl.SalesOrderLineID JOIN Item i ON i.ItemID = sl.ItemID "
        "JOIN SalesOrder so ON so.SalesOrderID = s.SalesOrderID JOIN Customer c ON c.CustomerID = so.CustomerID "
        "LEFT JOIN SalesInvoiceLine sil ON sil.ShipmentLineID = sl.ShipmentLineID WHERE sil.SalesInvoiceLineID IS NULL")]


@lru_cache(maxsize=None)
def cutoff(d, year: int) -> dict:
    """Revenue that belongs to a year and was posted later or never invoiced: its total and its split by segment and by
    item group."""
    invoices = [i for i in late(d) if i["year"] == year]
    lines = [u for u in unbilled(d) if u["delivered"][:4] == str(year)]
    segment, group = defaultdict(float), defaultdict(float)
    for i in invoices:
        segment[i["segment"]] += i["sub"]
        for g, v in i["groups"].items():
            group[g] += v
    for u in lines:
        segment[u["segment"]] += u["value"]
        group[u["group"]] += u["value"]
    return dict(invoices=invoices, lines=lines, n=len(invoices), n_lines=len(lines),
                total=xr(sum(i["sub"] for i in invoices) + sum(u["value"] for u in lines)),
                tax=xr(sum(i["tax"] for i in invoices)), std=xr(sum(u["std"] for u in lines)),
                segments=[(s, xr(v)) for s, v in sorted(segment.items())],
                groups=[(g, xr(group[g])) for g in ordered_groups(group)], segment=dict(segment), group=dict(group))


def register_cost(d, period: int) -> dict:
    gross, tax, ben, mfg = d.q("SELECT SUM(pr.GrossPay), SUM(pr.EmployerPayrollTax), SUM(pr.EmployerBenefits), "
                               "SUM(CASE WHEN c.CostCenterName = 'Manufacturing' THEN pr.GrossPay + pr.EmployerPayrollTax "
                               "+ pr.EmployerBenefits ELSE 0 END) FROM PayrollRegister pr JOIN CostCenter c ON c.CostCenterID = "
                               "pr.CostCenterID WHERE pr.PayrollPeriodID = ?", period)[0]
    return dict(gross=gross or 0.0, tax=tax or 0.0, ben=ben or 0.0, mfg=mfg or 0.0,
                total=(gross or 0.0) + (tax or 0.0) + (ben or 0.0))


@lru_cache(maxsize=None)
def payroll(d, year: int) -> dict:
    """The cost of a year's last days of work paid in the next fiscal year, by working day."""
    end = ye(year)
    full = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate, PayDate FROM PayrollPeriod WHERE PeriodEndDate <= ? "
               "AND PayDate > ? ORDER BY PeriodStartDate", end, end)
    cross = d.q("SELECT PayrollPeriodID, PeriodStartDate, PeriodEndDate, PayDate FROM PayrollPeriod WHERE PeriodStartDate <= ? "
                "AND PeriodEndDate > ? ORDER BY PeriodStartDate", end, end)
    periods = full + cross
    registered = bool(periods) and all(d.one("SELECT COUNT(*) FROM PayrollRegister WHERE PayrollPeriodID = ?", p[0]) > 0
                                       for p in periods)
    if year != d.C:     # Requirement 4: the registers at the earlier year-ends, the processed periods' rate at the last
        none = dict(id="?", start="?", end="?", pay="?")
        parts = []
        for p in full:
            parts.append((dict(id=p[0], start=p[1], end=p[2], pay=p[3]), register_cost(d, p[0]), 1.0, None, None))
        for p in cross:
            inside, span = working_days(d, p[1], end), working_days(d, p[1], p[2])
            parts.append((dict(id=p[0], start=p[1], end=p[2], pay=p[3]), register_cost(d, p[0]), inside / span, inside, span))
        tot = {k: sum(c[k] * share for _, c, share, _, _ in parts) for k in ("total", "gross", "tax", "ben", "mfg")}
        f = next((q for q in parts if q[3] is None), (none, dict(total=0.0), 0.0, None, None))
        x = next((q for q in parts if q[3] is not None), (none, dict(total=0.0), 0.0, 0, 0))
        return dict(method="registers", n_full=len(full), n_cross=len(cross), registered=registered,
                    full=dict(f[0], cost=xr(f[1]["total"])),
                    cross=dict(x[0], inside=x[3], days=x[4], share=xr(x[1]["total"] * x[2])),
                    total=xr(tot["total"]), gross=xr(tot["gross"]), tax=xr(tot["tax"]), ben=xr(tot["ben"]),
                    mfg=xr(tot["mfg"]), other=xr(tot["total"] - tot["mfg"]))
    p = processed(d)
    mfg = next((c["amount"] for c in p["centers"] if c["name"] == "Manufacturing"), 0.0)
    return dict(method="processed", n_full=len(full), n_cross=len(cross), registered=registered, p=p, total=p["accrual"],
                gross=p["gross"], tax=p["tax"], ben=p["ben"], mfg=mfg, other=xr(p["accrual"] - mfg),
                periods=[q[0] for q in periods])


@lru_cache(maxsize=None)
def notes_payable(d) -> list[dict]:
    """The debt agreements in origination order, with their schedules."""
    out = []
    for aid, number, asset, origin, principal, rate_, term, start, payment in d.q(
            "SELECT da.DebtAgreementID, da.AgreementNumber, fa.AssetCode, da.OriginationDate, da.PrincipalAmount, "
            "da.AnnualInterestRate, da.TermMonths, da.PaymentStartDate, da.ScheduledPaymentAmount FROM DebtAgreement da "
            "LEFT JOIN FixedAsset fa ON fa.FixedAssetID = da.FixedAssetID ORDER BY da.OriginationDate, da.DebtAgreementID"):
        lines = [dict(date=dt, principal=p, interest=i, status=s, je=je) for dt, p, i, s, je in d.q(
            "SELECT PaymentDate, PrincipalAmount, InterestAmount, Status, JournalEntryID FROM DebtScheduleLine "
            "WHERE DebtAgreementID = ? ORDER BY PaymentDate", aid)]
        out.append(dict(id=aid, number=number, asset=asset, origin=origin, principal=principal, rate=rate_, term=term,
                        start=start, payment=payment, lines=lines))
    return out


def outstanding(n: dict, asof: str) -> float:
    return xr(sum(line["principal"] for line in n["lines"] if line["date"] > asof)) if n["origin"] <= asof else 0.0


@lru_cache(maxsize=None)
def interest(d, year: int) -> dict:
    """Interest accrued at a year-end: each payment's interest covers the days since the payment before it, so the
    year-end carries the share of the next payment from the previous payment (counted inclusive) to the year-end."""
    end = ye(year)
    items = []
    for k, n in enumerate(notes_payable(d), 1):
        if n["origin"] > end:
            continue
        nxt = next((line for line in n["lines"] if line["date"] > end), None)
        if nxt is None:
            continue
        prev = max([line["date"] for line in n["lines"] if line["date"] <= end] + [n["origin"]])
        span, elapsed = days(prev, nxt["date"]), days(prev, end) + 1
        share = min(elapsed, span) / span
        items.append(dict(note=k, date=nxt["date"], prev=prev, interest=nxt["interest"], span=span, elapsed=elapsed,
                          full=elapsed >= span, amount=xr(nxt["interest"] * share),
                          alt=xr(nxt["interest"] * (1 if elapsed >= span else (elapsed - 1) / span))))
    return dict(items=items, total=xr(sum(i["amount"] for i in items)), alt=xr(sum(i["alt"] for i in items)))


# --- Requirement 5: the adjustments ---------------------------------------------------------------------

@lru_cache(maxsize=None)
def adjustments(d) -> dict:
    F, P, C = d.F, d.P, d.C
    pay = {y: payroll(d, y) for y in (F, P, C)}
    cut = {y: cutoff(d, y)["total"] for y in (F, P, C)}
    old = {y: stale(d, y) for y in (F, P, C)}
    intr = {y: interest(d, y)["total"] for y in (F, P, C)}
    a = dict(
        A1=dict(re=-pay[F]["total"], P=-(pay[P]["total"] - pay[F]["total"]), C=-(pay[C]["total"] - pay[P]["total"])),
        A2=dict(re=cut[F], P=cut[P] - cut[F], C=cut[C] - cut[P]),
        A3=dict(re=old[F], P=old[P] - old[F], C=old[C] - old[P]),
        A4=dict(re=-intr[F], P=intr[F] - intr[P], C=intr[P] - intr[C]))
    a = {k: {kk: xr(vv) for kk, vv in v.items()} for k, v in a.items()}
    total = {k: xr(sum(v[k] for v in a.values())) for k in ("re", "P", "C")}
    split = {y: dict(cogs=xr(pay[y]["mfg"] - pay[y - 1]["mfg"]), opx=xr(pay[y]["other"] - pay[y - 1]["other"])) for y in (P, C)}
    return dict(a=a, total=total, pay=pay, cut=cut, old=old, intr=intr, split=split,
                equity={P: xr(total["re"] + total["P"]), C: xr(total["re"] + total["P"] + total["C"])},
                adj_ni={P: xr(net_income(d, P) + total["P"]), C: xr(net_income(d, C) + total["C"])})


def current_portion(d, year: int) -> float:
    return xr(sum(sum(line["principal"] for line in n["lines"] if line["date"][:4] == str(year + 1))
                  for n in notes_payable(d) if n["origin"] <= ye(year)))


@lru_cache(maxsize=None)
def statement(d, year: int) -> dict:
    """The adjusted balance sheet at a year-end (with A1-A4 cumulative to that date, R1 and R2)."""
    adj = adjustments(d)
    t = lambda nums: bal(d, nums, ye(year))
    cash = xr(t(CASH))
    recv = xr(t(RECEIVABLES) + adj["cut"][year])
    fg, mat, wip = xr(t(["1040"])), xr(t(["1045"])), xr(t(["1046", "1090"]))
    inv = xr(t(INVENTORIES))
    prepaid = xr(t(PREPAID))
    ca = xr(cash + recv + inv + prepaid)
    ppe = xr(t(accounts_of(d, "Fixed Asset", "Contra Fixed Asset", "Noncurrent Asset")))
    ap, grni = xr(-t(PAYABLES)), xr(-t(["2020"]))
    payroll_ = xr(-t(PAYROLL) + adj["pay"][year]["total"])
    comm = xr(-t(COMMISSIONS))
    accexp = xr(-t(ACCRUED) - adj["old"][year])
    intr = adj["intr"][year]
    accrued = xr(payroll_ + comm + accexp + intr)
    stax, credits = xr(-t(SALES_TAX)), xr(-t(CREDITS))
    cur = current_portion(d, year)
    cl = xr(ap + grni + accrued + stax + credits + cur)
    notes = xr(-t(["2110"]))
    lt = xr(notes - cur)
    tl = xr(cl + lt)
    re = xr(-t(["3030"]) + net_income(d, year) + (adj["equity"][year] if year in adj["equity"] else adj["total"]["re"]))
    stock = xr(-t(["3010"]))
    return dict(cash=cash, recv=recv, fg=fg, mat=mat, wip=wip, inv=inv, prepaid=prepaid, ca=ca, ppe=ppe, ta=xr(ca + ppe),
                ap=ap, grni=grni, payroll=payroll_, comm=comm, accexp=accexp, intr=intr, accrued=accrued, stax=stax,
                credits=credits, cur=cur, cl=cl, notes=notes, lt=lt, tl=tl, re=re, stock=stock, equity=xr(re + stock),
                wc=xr(ca - cl), cr=ca / cl, qr=(cash + recv) / cl, cash_net=xr(cash - stax))


@lru_cache(maxsize=None)
def adjusted_income(d, year: int) -> dict:
    adj = adjustments(d)
    k = "P" if year == d.P else "C"
    i = income(d, year)
    opr = xr(i["opr"] + adj["a"]["A2"][k])
    cogs = xr(i["cogs"] + adj["split"][year]["cogs"])
    opx = xr(i["opx"] + adj["split"][year]["opx"] - adj["a"]["A3"][k])
    intr = xr(i["intr"] - adj["a"]["A4"][k])
    net_rev = xr(opr - i["ret"])
    gm = xr(net_rev - cogs)
    op = xr(gm - opx)
    return dict(opr=opr, ret=i["ret"], net_rev=net_rev, cogs=cogs, gm=gm, opx=opx, op=op, intr=intr, loss=i["loss"],
                ni=xr(op - intr - i["loss"]))


def wc_lines(d, year: int) -> dict:
    """The working-capital balances of the adjusted statements at a year-end, for the cash flow statement."""
    adj = adjustments(d)
    t = lambda nums: bal(d, nums, ye(year))
    special = set(CASH + RECEIVABLES + INVENTORIES + PAYABLES + ["2020"] + SALES_TAX)
    other_assets = [n for n in accounts_of(d, "Current Asset", "Contra Current Asset") if n not in special]
    other_liabilities = [n for n in accounts_of(d, "Current Liability") if n not in special]
    return dict(recv=t(RECEIVABLES) + adj["cut"][year], inv=t(INVENTORIES), pay=-t(PAYABLES + ["2020"]), stax=-t(SALES_TAX),
                other=-t(other_liabilities) - t(other_assets) + adj["pay"][year]["total"] - adj["old"][year] + adj["intr"][year])


@lru_cache(maxsize=None)
def cash_flows(d, year: int) -> dict:
    a, b = wc_lines(d, year - 1), wc_lines(d, year)
    adj = adjustments(d)
    r = restated(d, year)
    dep = xr(activity(d, ["6130"], year) + d.one(
        "SELECT COALESCE(SUM(g.Debit), 0) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID AND "
        "g.SourceDocumentType = 'JournalEntry' WHERE j.EntryType = 'Depreciation' AND g.AccountID = ? AND g.FiscalYear = ?",
        d.account("1090"), year))
    out = dict(ni=adj["adj_ni"][year], dep=dep, loss=income(d, year)["loss"],
               recv=xr(-(b["recv"] - a["recv"])), inv=xr(-(b["inv"] - a["inv"])), pay=xr(b["pay"] - a["pay"]),
               stax=xr(b["stax"] - a["stax"]), other=xr(b["other"] - a["other"]))
    out["operating"] = xr(sum(out.values()))
    out.update(investing=r["investing"], financing=r["financing"], recorded_operating=r["operating"],
               proceeds=xr(r["proceeds"]), paid=xr(r["proceeds"] - r["investing"]), notes_financed=xr(r["notes_financed"]),
               depreciation_entries=r["depreciation"])
    dr, cr = flow(d, CASH, f"{year}-01-01", ye(year))
    out["cash"] = xr(dr - cr)
    out["interest_paid"] = xr(d.one(
        "SELECT COALESCE(SUM(g.Debit), 0) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID AND "
        "g.SourceDocumentType = 'JournalEntry' WHERE j.EntryType = 'Interest Payment' AND g.AccountID = ? AND g.FiscalYear = ?",
        d.account("7030"), year))
    return out


# --- shared claims ---------------------------------------------------------------------------------------

def claim_payroll_routing(d, claim) -> None:
    """Where the current year's payroll is debited: Manufacturing to 1090, the others to salary accounts and 6060."""
    accounts = {}
    for center, number in d.q("SELECT DISTINCT c.CostCenterName, a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = "
                              "g.AccountID JOIN CostCenter c ON c.CostCenterID = g.CostCenterID WHERE g.SourceDocumentType = "
                              "'PayrollSummary' AND g.Debit > 0 AND g.FiscalYear = ?", d.C):
        accounts.setdefault(center, set()).add(str(number))
    claim(accounts.get("Manufacturing") == {"1090"}, "the manufacturing payroll is debited to 1090")
    claim(all(a & {"6060"} and all(chart(d)[n]["name"].startswith("Salaries Expense") for n in a - {"6060"})
              for c, a in accounts.items() if c != "Manufacturing"),
          "the other cost centers' payroll goes to their salary accounts and 6060")


def claim_opening(d, claim) -> None:
    """The balances that rest on the opening entry have no document and have not changed."""
    entry = opening_entry(d)
    a1050 = d.account("1050")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND VoucherNumber <> ?", a1050, entry) == 0,
          "the opening line is the only posting to 1050")
    claim(abs(d.one("SELECT COALESCE(SUM(Debit - Credit), 0) FROM GLEntry WHERE AccountID = ? AND VoucherNumber <> ?",
                    d.account("2030"), entry)) < 0.005, "every posting to 2030 but the opening line nets to zero")
    opening_cash = opening_line(d, "1010")
    claim(abs(opening_line(d, "2010") - opening_cash) < 0.005, "the opening payables equal the opening cash line to the cent")
    asof = ye(d.C)
    receivable = xr(sum(i["balance"] for i in open_invoices(d)))
    claim(abs(bal(d, ["1020"], asof) - receivable - opening_line(d, "1020")) < 0.005,
          "the receivables ledger exceeds the open invoices by exactly the opening line")
    open_ap = xr(d.one("SELECT SUM(b) FROM (SELECT pi.GrandTotal - COALESCE((SELECT SUM(p.Amount) FROM DisbursementPayment p "
                       "WHERE p.PurchaseInvoiceID = pi.PurchaseInvoiceID AND p.PaymentDate <= ?1), 0) AS b FROM PurchaseInvoice pi "
                       "WHERE pi.InvoiceDate <= ?1) WHERE b > 0", asof))
    reclassed = sum(c["amount"] for c in capital_invoices(d, asof))
    claim(abs(open_ap - reclassed + opening_line(d, "2010") + bal(d, ["2010"], asof)) < 0.005,
          "the payables ledger is the open invoices less the reclassified ones plus the opening line")
    c = composition(d, d.C)
    claim(abs(c["total"] - c["ledger"]) < 0.005, "2040 still holds its opening line")


# --- the milestones -----------------------------------------------------------------------------------------

@note("ch17.m1", CHAPTER)
def m1(d, claim):
    ys = [d.F, d.P, d.C]
    claim(no_tax_account(d), "the chart has no income tax account")
    return dict(rec=[recorded(d, y) for y in ys], ni=[net_income(d, y) for y in ys], never=len(never_posted(d)))


@note("ch17.m2", CHAPTER)
def m2(d, claim):
    ys = [d.F, d.P, d.C]
    comp = [composition(d, y) for y in ys]
    claim(all(abs(c["total"] - c["ledger"]) < 0.005 for c in comp), "the parts of 2040 add up to the ledger at each year-end")
    adj = adjustments(d)
    return dict(comp=comp, opening=comp[0]["opening"], cut=[adj["cut"][y] for y in ys],
                pay=[adj["pay"][y]["total"] for y in ys], intr=[adj["intr"][y] for y in ys], total=adj["total"],
                mat_c=materiality(d, d.C), mat_p=materiality(d, d.P))


@note("ch17.m3", CHAPTER)
def m3(d, claim):
    adj = adjustments(d)
    s_c, s_p = statement(d, d.C), statement(d, d.P)
    cf = cash_flows(d, d.C)
    reported = xr(recorded(d, d.F)["re"] + net_income(d, d.F))
    cost = xr(bal(d, accounts_of(d, "Fixed Asset"), ye(d.C)))
    accumulated = xr(-bal(d, accounts_of(d, "Contra Fixed Asset"), ye(d.C)))
    return dict(adj_ni=adj["adj_ni"], s_c=s_c, s_p=s_p, reported=reported, restated=xr(reported + adj["total"]["re"]),
                cf=cf, cost=cost, accumulated=accumulated)


@note("ch17.m4", CHAPTER)
def m4(d, claim):
    after = ye(d.C)
    payments, amount = d.q("SELECT COUNT(*), SUM(Amount) FROM DisbursementPayment WHERE PaymentDate > ?", after)[0]
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE ReceivedDate > ?", after) == 0,
          f"no supplier invoice was received after {d.C}, so no unrecorded liability is found")
    claim(no_tax_account(d), "there is no income tax account")
    stax = xr(-bal(d, SALES_TAX, after))
    equity = xr(sum(opening_line(d, n) for n in ("2010", "2030", "2040")) - sum(opening_line(d, n) for n in ("1020", "1050")))
    claim(equity > 0, "equity rises if none of the opening balances is real")
    return dict(payments=payments, amount=xr(amount), stax=stax, equity=equity)


# --- Requirement 1 -------------------------------------------------------------------------------------------

@note("ch17.r1", CHAPTER)
def r1(d, claim):
    ys = [d.F, d.P, d.C]
    closes = []
    for y in ys:
        c = d.closes_of(y)
        claim(len(c) == 2, f"two closes are dated at the end of {y}")
        closes.append(f"{c[0]}/{int(c[-1].rsplit('-', 1)[1])}" if c else "?")
    claim(len(d.closes) == 2 * len(ys), "every close is dated at a year-end of the window")
    rec = [recorded(d, y) for y in ys]
    claim(all(abs(r["debits"] - r["credits"]) < 0.005 for r in rec), "debit and credit balances are equal at each year-end")
    ni = [net_income(d, y) for y in ys]
    a3030 = d.account("3030")
    for y, n in zip(ys, ni):
        to_re = d.one("SELECT SUM(g.Credit - g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
                      "AND g.SourceDocumentType = 'JournalEntry' WHERE j.EntryType LIKE 'Year-End Close - Income Summary%' "
                      "AND g.AccountID = ? AND g.PostingDate = ?", a3030, ye(y))
        claim(to_re is not None and abs(to_re - n) < 0.005, f"net income of {y} equals its Income Summary close to 3030")
    claim(chart(d)["2110"]["sub"] == "Long-Term Liability", "2110 is classified as a long-term liability")
    claim(len({r["stock"] for r in rec}) == 1, "common stock is the same at each year-end")
    inc = [income(d, y) for y in (d.P, d.C)]
    claim(all(abs(i["ni"] - net_income(d, y)) < 0.005 for i, y in zip(inc, (d.P, d.C))),
          "the income lines add up to net income (no other income or expense)")
    claim(all(abs(activity(d, [n for n in accounts_of(d, "Contra Revenue") if n != "4060"], y)) < 0.005 for y in (d.P, d.C)),
          "returns are the only contra revenue (4060)")
    never = never_posted(d)
    names = {n: nm for n, nm, _ in never}
    active = [n for n, _, a in never if a]
    inactive = [n for n, _, a in never if not a]
    label = lambda n: f"{n} {names[n]}" if n in NAMED else n
    claim(NAMED <= set(names), "every account the note names is among the never-posted accounts")
    claim(all(n in names for n in LEADS), "2080, 2120, 1140, 1030, and 7010 are unused")
    claim(no_tax_account(d), "the chart has no income tax account")
    taxes = [nm for (nm,) in d.q("SELECT AccountName FROM Account WHERE AccountName LIKE '%Tax%'")]
    claim(taxes and all("Sales Tax" in nm or "Payroll Tax" in nm for nm in taxes),
          "the accounts named for taxes are sales tax and payroll taxes")
    return dict(closes=closes, rec=rec, ni=ni, inc=inc, n_never=len(never), n_active=len(active),
                active=", ".join(label(n) for n in active), n_inactive=len(inactive),
                inactive=", ".join(label(n) for n in inactive))


# --- Requirement 2 -------------------------------------------------------------------------------------------

@note("ch17.r2", CHAPTER)
def r2(d, claim):
    mat_c, mat_p = materiality(d, d.C), materiality(d, d.P)
    tp, tc = tb(d, ye(d.P)), tb(d, ye(d.C))
    pl = set(pl_accounts(d))
    changes = []
    for n in set(tp) | set(tc):
        if n == "3030":
            continue
        delta = activity(d, [n], d.C) - activity(d, [n], d.P) if n in pl else tc.get(n, 0.0) - tp.get(n, 0.0)
        changes.append((abs(xr(delta)), n, xr(delta)))
    changes.sort(key=lambda c: (-c[0], c[1]))
    above = [dict(n=n, credit=chart(d)[n]["normal"] == "Credit", v=-v if chart(d)[n]["normal"] == "Credit" else v)
             for a, n, v in changes if a > mat_c]
    following = [dict(n=n, v=a) for a, n, v in changes if a <= mat_c][:2]
    claim(all(abs(t.get(n, 0.0) - activity(d, [n], y)) < 0.005 for y, t in ((d.P, tp), (d.C, tc)) for n in pl),
          "at a year-end a revenue or expense account's balance is that year's activity")
    re_change = -(tc.get("3030", 0.0) - tp.get("3030", 0.0))
    claim(abs(re_change - net_income(d, d.P)) < 0.005 and abs(re_change) > mat_c,
          f"retained earnings moves by {d.P}'s net income, closed into it, above materiality")
    entry = opening_entry(d)
    lines = d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber = ? AND SourceDocumentType = 'JournalEntry'", entry)
    claim_opening(d, claim)
    claim({r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? AND VoucherNumber <> ?",
                             d.account("2030"), entry)} <= {"PayrollSummary", "PayrollPayment"},
          "the other postings to 2030 are payroll postings")
    a1110 = d.account("1110")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", a1110) == 1, "1110 has a single posting")
    assets = d.q("SELECT AssetCode, OriginalCost FROM FixedAsset WHERE AssetAccountID = ?", a1110)
    claim(len(assets) == 1 and abs(assets[0][1] - bal(d, ["1110"], ye(d.C))) < 0.005,
          "the FixedAsset register supports 1110's posting with one asset")
    grew = xr(-(tc.get("2040", 0.0) - tp.get("2040", 0.0)))
    claim(grew > 0, "2040 grew")
    claim(tc.get("1090", 0.0) < 0 and chart(d)["1090"]["sub"] == "Current Asset", "1090 has a credit balance inside current assets")
    unused = {n for n, _, _ in never_posted(d)}
    claim({"1030", "2120", "1140", "7010"} <= unused, "1030, 2120, 1140, and 7010 are unused")
    debits = [r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? AND Debit > 0",
                                d.account("2050"))]
    claim(debits == ["CreditMemo"], "2050 has no debits except credit memos")
    rent = d.q("SELECT substr(PostingDate, 1, 4), COUNT(DISTINCT substr(PostingDate, 1, 7)) FROM JournalEntry WHERE EntryType = 'Rent' "
              "GROUP BY 1")
    claim(len(rent) == len(d.years) and all(n == 12 for _, n in rent), "rent is paid every month")
    claim(no_tax_account(d), "there is no tax account")
    cash = bal(d, CASH, ye(d.C))
    claim(cash > 1_000_000, "cash is more than a million")
    return dict(mat_c=mat_c, mat_p=mat_p, above=above, following=following, entry=entry, lines=lines,
                names={n: chart(d)[n]["name"] for n in ("1050", "2030")},
                prepaid=opening_line(d, "1050"), payroll=opening_line(d, "2030"), receivable=opening_line(d, "1020"),
                payable=opening_line(d, "2010"), accrued=opening_line(d, "2040"),
                asset=assets[0][0] if assets else "?", asset_cost=assets[0][1] if assets else 0.0, grew=grew,
                millions=int(cash // 1_000_000))


# --- Requirement 3 -------------------------------------------------------------------------------------------

@note("ch17.r3", CHAPTER)
def r3(d, claim):
    acc = accruals(d)
    entries = list(acc["entries"].values())
    claim(all(a["debits"] == 1 and a["credits"] == 1 and a["other"] == 0 for a in entries),
          "each Accrual entry credits 2040 and debits one expense account")
    debit_accounts = sorted({a["account"] for a in entries})
    per = defaultdict(int)
    for jid, *_ in acc["lines"]:
        per[jid] += 1
    claim(max(per.values()) == 1, "at most one invoice line per accrual")
    claim(set(per) <= set(acc["entries"]), "every AccrualJournalEntryID is an Accrual entry")
    kinds = d.q("SELECT SUM(pi.PurchaseOrderID IS NULL), SUM(pi.InvoiceNumber LIKE 'ASV%'), COUNT(*) FROM PurchaseInvoiceLine l "
                "JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = l.PurchaseInvoiceID WHERE l.AccrualJournalEntryID IS NOT NULL")[0]
    claim(kinds[0] == kinds[2] and kinds[1] == kinds[2], "all the referring lines are on ASV service invoices with no purchase order")
    n_lines = d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE AccrualJournalEntryID IS NOT NULL")
    claim(n_lines == len(acc["lines"]), "every referring line has its debit to 2040")
    null_lines = d.one("SELECT COUNT(*) FROM PurchaseInvoiceLine WHERE AccrualJournalEntryID IS NULL")
    adj = acc["adjustments"]
    excess = d.q("SELECT g.FiscalYear, COUNT(DISTINCT l.PILineID), SUM(g.Debit) FROM PurchaseInvoiceLine l JOIN GLEntry g "
                 "ON g.SourceDocumentType = 'PurchaseInvoice' AND g.SourceLineID = l.PILineID JOIN Account a ON a.AccountID = g.AccountID "
                 "WHERE l.AccrualJournalEntryID IS NOT NULL AND a.AccountType = 'Expense' AND g.Debit > 0 GROUP BY 1 ORDER BY 1")
    claim([r[0] for r in excess] == d.years, "the excess went to expense in each year of the window")
    a2040 = d.account("2040")
    split_lines = d.q("SELECT l.LineTotal, SUM(CASE WHEN g.AccountID = ?1 THEN g.Debit ELSE 0 END), SUM(CASE WHEN a.AccountType = "
                      "'Expense' THEN g.Debit ELSE 0 END), l.AccrualJournalEntryID FROM PurchaseInvoiceLine l JOIN GLEntry g "
                      "ON g.SourceDocumentType = 'PurchaseInvoice' AND g.SourceLineID = l.PILineID JOIN Account a "
                      "ON a.AccountID = g.AccountID WHERE l.AccrualJournalEntryID IS NOT NULL GROUP BY l.PILineID", a2040)
    claim(all(abs(t - cl - ex) < 0.005 and (ex < 0.005 or cl >= acc["entries"][j]["amount"] - 0.005)
              for t, cl, ex, j in split_lines if j in acc["entries"]),
          "each invoice line clears its accrual through 2040 and charges only the excess to expense")
    lags = acc["lags"]
    window = acc["window"]
    at_window = lags.count(window)
    claim(at_window > 1, "more than one accrual cleared at exactly the longest lag")
    # the rule of "older than the last two month-ends" against the window rule: the accruals it flags inside the window,
    # and those of them that an invoice cleared after the year-end (wrongly flagged)
    wrong, early_open = [], []
    for y in d.years:
        for a in acc["entries"].values():
            if not (a["date"] < f"{y}-11-01" and days(a["date"], ye(y)) <= window and open_amount(a, ye(y)) > 0.004):
                continue
            early_open.append(a["number"])
            later = sorted((c for c in a["clear"] if c["kind"] == "invoice" and c["date"] > ye(y)), key=lambda c: c["date"])
            if later:
                wrong.append(dict(year=y, number=a["number"], age=days(a["date"], ye(y)), cleared=later[0]["date"],
                                  invoice=later[0]["doc"]))
    claim(bool(wrong) or not early_open, "with none wrongly flagged, no accrual inside the window was open at a year-end")
    comp = [composition(d, y) for y in d.years]
    claim(all(c["excess"] > 0 for c in comp), "freight not yet settled exceeds December's freight at each year-end")
    settlements = d.q("SELECT j.PostingDate, j.TotalAmount, substr(j.Description, -7) FROM JournalEntry j "
                      "WHERE j.EntryType = 'Freight Settlement' ORDER BY 1")
    claim(all(s[0] == first_weekday(s[0]) and s[2] == month_before(s[0]) for s in settlements),
          "each settlement posts on the first weekday of the month after the freight it settles")
    claim(max(s[0] for s in settlements) <= ye(d.C) and all(s[2] != f"{d.C}-12" for s in settlements),
          f"no settlement of December {d.C}'s freight is in the data")
    settled = d.one("SELECT SUM(g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID AND "
                    "g.SourceDocumentType = 'JournalEntry' WHERE g.AccountID = ? AND j.EntryType = 'Freight Settlement'", a2040)
    claim(abs(settled - sum(s[1] for s in settlements)) < 0.005, "the settlements' totals are their debits to 2040")
    shipped = d.one("SELECT SUM(Credit) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'Shipment'", a2040)
    freight_out = d.one(f"SELECT SUM(Debit - Credit) FROM GLEntry WHERE AccountID = ? AND {d.no_closes()}", d.account("5050"))
    claim(abs(shipped - freight_out) < 0.005, "shipment credits to 2040 equal the 5050 debits")
    claim(all(abs(c["total"] - c["ledger"]) < 0.005 for c in comp), "the composition equals the ledger at each year-end")
    last = comp[-1]
    claim(not any(invoiced(i) for i in last["old_items"]), f"the old items at {d.C} were never invoiced")
    cleanups = [a for a in adj if a[4].startswith("Partial cleanup")]
    old_ids = {i["id"] for i in last["old_items"]}
    claim(all(a[0] in old_ids for a in cleanups), "the partial cleanups were of old items")
    cleanup_entries = [a[3] for a in sorted(cleanups, key=lambda a: a[3])]
    claim(all(not invoiced(acc["entries"][a[0]]) for a in cleanups), "the partly cleaned items have no invoice")
    by_year, by_account = defaultdict(lambda: [0.0, 0]), defaultdict(float)
    for i in last["old_items"]:
        by_year[int(i["date"][:4])][0] += i["open"]
        by_year[int(i["date"][:4])][1] += 1
        by_account[i["account"]] += i["open"]
    claim(sorted(by_year) == d.years, "old items were recorded in each year of the window")
    # young items at the earlier year-ends that were never invoiced
    young = {}
    for y in (d.F, d.P):
        items = [i for i in composition(d, y)["young_items"] if not invoiced(i)]
        young[y] = dict(items=items, entries=[i["number"] for i in items],
                        left=xr(sum(open_amount(i, ye(d.C)) for i in items)),
                        cleaned=[i for i in items if open_amount(i, ye(d.C)) < i["open"] - 0.004])
    claim(not young[d.F]["cleaned"], f"none of the young items of {d.F} never invoiced was cleaned up")
    yp = young[d.P]["items"]
    claim(len(yp) == 1 and len(young[d.P]["cleaned"]) == 1, f"one young item of {d.P} was never invoiced, and it was partly cleaned up")
    p_item = yp[0] if yp else dict(number="?", open=0.0, clear=[])
    cleaned_in = min((c["date"] for c in p_item["clear"] if c["kind"] == "adjustment" and c["date"] > ye(d.P)), default="?")[:4]
    for y in (d.F, d.P):
        claim(any(i["date"][:4] == str(y) and i["date"][5:7] in ("11", "12") and days(i["date"], ye(y)) <= window
                  for i in last["old_items"]),
              f"the old items include ones recorded in November or December {y}, young at that year-end")
    a3 = adjustments(d)["a"]["A3"]
    return dict(n=len(entries), amount=xr(sum(a["amount"] for a in entries)), low=debit_accounts[0], high=debit_accounts[-1],
                n_lines=n_lines, cleared=xr(sum(r[2] for r in acc["lines"])), null_lines=null_lines,
                n_adj=len(adj), targets=len({a[0] for a in adj}), adj_amount=xr(sum(a[2] for a in adj)),
                excess=[xr(r[2]) for r in excess], excess_lines=[r[1] for r in excess],
                lag_low=lags[0], lag_high=window, median=lags[len(lags) // 2], at_window=word(at_window), window=window,
                wrong=wrong, comp=comp, opening=comp[0]["opening"], settlements=len(settlements),
                settled=xr(sum(s[1] for s in settlements)), shipped=xr(shipped),
                n_old=last["n_old"], cleanups=len(cleanups), cleanup_entries=cleanup_entries,
                by_year=[(y, xr(v[0]), v[1]) for y, v in sorted(by_year.items())],
                origin=[xr(v[0]) for _, v in sorted(by_year.items())],
                by_account=[(n, xr(v)) for n, v in sorted(by_account.items())],
                young_f=young[d.F], young_f_entries=abbreviated(young[d.F]["entries"]), young_p=young[d.P],
                p_item=p_item, cleaned_in=cleaned_in, a3=a3, young_c=last["young"])


# --- Requirement 4 -------------------------------------------------------------------------------------------

@note("ch17.r4", CHAPTER)
def r4(d, claim):
    cf, cp, cc = cutoff(d, d.F), cutoff(d, d.P), cutoff(d, d.C)
    claim(cf["n_lines"] == 0 and cp["n_lines"] == 0, f"no shipment of {d.F} or {d.P} was left unbilled")
    claim(cc["n"] == 0, f"no invoice for {d.C} deliveries was posted later")
    claim(all(int(i["posted"][:4]) == i["year"] + 1 for i in late(d)), "each late invoice is posted in the year after the delivery")
    # freight billed on the late invoices (left out of the SubTotal measure; trivial if any)
    freight = [i for i in late(d) if abs(i["freight"]) >= 0.005]
    late_freight = xr(sum(i["freight"] for i in freight))
    claim(abs(late_freight) < TRIVIAL * materiality(d, d.C), "the freight on the late invoices is clearly trivial")
    # the late invoices dated in the year of the delivery (posted in the next year): the cutoff errors of Chapter 6
    dated = {y: [i["number"] for i in x["invoices"] if i["date"][:4] == str(y)] for y, x in ((d.F, cf), (d.P, cp))}
    claim(all(u["shipped"][:7] == f"{d.C}-12" for u in unbilled(d)), f"the lines never invoiced shipped in December {d.C}")
    ids = ",".join(str(u["id"]) for u in unbilled(d)) or "NULL"
    posted = d.one(f"SELECT COALESCE(SUM(g.Debit), 0) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                   f"WHERE g.SourceDocumentType = 'Shipment' AND a.AccountSubType = 'COGS' AND g.SourceLineID IN ({ids}) "
                   f"AND g.PostingDate <= ?", ye(d.C))
    claim(abs(posted - cc["std"]) < 0.005, "their standard cost is already in cost of goods sold")
    claim([r[0] for r in d.q("SELECT DISTINCT SourceDocumentType FROM GLEntry WHERE AccountID = ? AND Credit > 0",
                             d.account("2050"))] == ["SalesInvoice"], "sales tax is recorded on invoicing")
    pf, pp, pc = payroll(d, d.F), payroll(d, d.P), payroll(d, d.C)
    for y, x in ((d.F, pf), (d.P, pp)):
        claim(x["registered"] and x["n_full"] == 1 and x["n_cross"] == 1,
              f"at the end of {y} one registered period is paid in the next year and one crosses the year-end")
    claim(not pc["registered"], f"the pay periods of December {d.C} after the last processed one have no registers")
    claim(d.one("SELECT COUNT(*) FROM (SELECT CalendarDate FROM WorkCenterCalendar GROUP BY 1 "
                "HAVING SUM(IsWorkingDay) NOT IN (0, COUNT(*)))") == 0, "every work center has the same working days")
    claim_payroll_routing(d, claim)
    claim(chart(d)["5080"]["sub"] == "COGS", "5080 is part of cost of goods sold")
    hours = [round(late_december_cost(d, y), -3) for y in (d.F, d.P)]
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", d.account("2080")) == 0, "2080 has never been used")
    ints = [dict(interest(d, y), year=y) for y in (d.F, d.P, d.C)]
    claim(all(x["items"] for x in ints), "a note payment falls due after each year-end")
    for x in ints:
        prorated = [i for i in x["items"] if not i["full"]]
        # the other day count (the previous payment's day left out), named by its days when one payment is prorated
        x.update(prorated=bool(prorated), short=prorated[0]["elapsed"] - 1 if len(prorated) == 1 else None)
    last = max((k for k, x in enumerate(ints) if x["prorated"]), default=None)
    return dict(cf=cf, cp=cp, cc=cc, dated=dated, late_freight=late_freight, freight_invoices=[i["number"] for i in freight],
                pf=pf, pp=pp, pc=pc, hours=hours, ints=ints, last_prorated=last)


# --- Requirement 5 -------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def allowance(d) -> float:
    """Passed item P1: Exercise 8.1's allowance at its rates on the open invoices at the end of d.C."""
    amounts = [0.0] * len(BUCKETS)
    for inv in open_invoices(d):
        amounts[bucket_of(inv["days"])] += inv["balance"]
    return xr(sum(xr(xr(a) * rate_) for a, (_, rate_) in zip(amounts, BUCKETS)))


@lru_cache(maxsize=None)
def allowance_at(d, year: int) -> float:
    """P1's allowance at another year-end: Tutorial 8.2's open invoices (invoices less the receipts applied and the credit
    memos dated on or before the year-end, rounded, kept if greater than zero), aged by due date at Exercise 8.1's rates."""
    asof = ye(year)
    amounts = [0.0] * len(BUCKETS)
    for due, balance in d.q("SELECT si.DueDate, si.GrandTotal - COALESCE((SELECT SUM(a.AppliedAmount) FROM CashReceiptApplication a "
                            "WHERE a.SalesInvoiceID = si.SalesInvoiceID AND a.ApplicationDate <= ?1), 0) - COALESCE((SELECT "
                            "SUM(c.GrandTotal) FROM CreditMemo c WHERE c.OriginalSalesInvoiceID = si.SalesInvoiceID AND "
                            "c.CreditMemoDate <= ?1), 0) FROM SalesInvoice si WHERE si.InvoiceDate <= ?1", asof):
        if xr(balance) > 0:
            amounts[bucket_of(days(due, asof))] += xr(balance)
    return xr(sum(xr(xr(a) * rate_) for a, (_, rate_) in zip(amounts, BUCKETS)))


@lru_cache(maxsize=None)
def returns_across(d) -> dict:
    """Returns made in a later fiscal year than the delivery of the goods returned: by return year, their count and
    credit-memo revenue (each return dated by the delivery of its first line), and their standard cost (by line)."""
    rows = d.q("SELECT CAST(substr(sr.ReturnDate, 1, 4) AS INTEGER), CAST(substr(s.DeliveryDate, 1, 4) AS INTEGER), "
               "COUNT(DISTINCT sr.SalesReturnID), SUM(cm.SubTotal) FROM SalesReturn sr JOIN CreditMemo cm ON cm.SalesReturnID = "
               "sr.SalesReturnID JOIN (SELECT SalesReturnID, MIN(ShipmentLineID) AS sl FROM SalesReturnLine GROUP BY 1) x "
               "ON x.SalesReturnID = sr.SalesReturnID JOIN ShipmentLine sl ON sl.ShipmentLineID = x.sl JOIN Shipment s "
               "ON s.ShipmentID = sl.ShipmentID WHERE substr(sr.ReturnDate, 1, 4) <> substr(s.DeliveryDate, 1, 4) GROUP BY 1, 2")
    cost = dict(d.q("SELECT CAST(substr(sr.ReturnDate, 1, 4) AS INTEGER), SUM(srl.ExtendedStandardCost) FROM SalesReturn sr "
                    "JOIN SalesReturnLine srl ON srl.SalesReturnID = sr.SalesReturnID JOIN ShipmentLine sl ON sl.ShipmentLineID = "
                    "srl.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE substr(sr.ReturnDate, 1, 4) <> "
                    "substr(s.DeliveryDate, 1, 4) GROUP BY 1"))
    return dict(pairs=[(r, dl) for r, dl, _, _ in rows], by_year={r: dict(n=n, rev=xr(rev), cost=xr(cost.get(r, 0.0)))
                                                                  for r, dl, n, rev in rows})


@note("ch17.r5", CHAPTER)
def r5(d, claim):
    adj = adjustments(d)
    a, total, split = adj["a"], adj["total"], adj["split"]
    pay_p, pay_c = adj["pay"][d.P], adj["pay"][d.C]
    cut_p, cut_c, old_p, old_c = adj["cut"][d.P], adj["cut"][d.C], adj["old"][d.P], adj["old"][d.C]
    intr_p, intr_c = adj["intr"][d.P], adj["intr"][d.C]
    # the entries at the year-end, each line as debits less credits; the side follows the sign
    entries = dict(
        A1=entry(("retained earnings", pay_p["total"]), ("5080", split[d.C]["cogs"]), ("operating expense", split[d.C]["opx"]),
                 ("2030", -pay_c["gross"]), ("2032", -pay_c["tax"]), ("2033", -pay_c["ben"])),
        A2=entry(("1020", cut_c), ("retained earnings", -cut_p), ("revenue", -a["A2"]["C"])),
        A3=entry(("2040", old_c), ("retained earnings", -old_p), ("operating expense", -a["A3"]["C"])),
        A4=entry(("retained earnings", intr_p), ("7030", -a["A4"]["C"]), ("2080", -intr_c)))
    for k, e in entries.items():
        claim(abs(sum(v for side, _, v in e if side == "Dr") - sum(v for side, _, v in e if side == "Cr")) < 0.005,
              f"{k}'s entry balances")
    accounts = revenue_accounts(d)
    by_group = defaultdict(float)
    for g, v in cutoff(d, d.C)["group"].items():
        by_group[g] += v
    for g, v in cutoff(d, d.P)["group"].items():
        by_group[g] -= v
    a2_accounts = sorted((accounts[g], xr(v)) for g, v in by_group.items())
    claim(abs(sum(v for _, v in a2_accounts) - a["A2"]["C"]) < 0.005, "A2's accounts add up to its effect")
    notes_ = notes_payable(d)
    claim(sum(1 for n in notes_ if n["origin"] <= ye(d.P)) == 1 and len(notes_) == 2 and notes_[1]["origin"][:4] == str(d.C),
          f"only note 1 existed at the end of {d.P}; note 2 began in {d.C}")
    c1090 = {y: xr(bal(d, ["1090"], ye(y))) for y in (d.P, d.C)}
    claim(all(v < 0 for v in c1090.values()), "1090 has a credit balance at both year-ends")
    mat_c, mat_p = materiality(d, d.C), materiality(d, d.P)
    claim(pay_c["total"] > mat_c, "the payroll liability exceeds materiality")
    s_c, s_p = statement(d, d.C), statement(d, d.P)
    r_c, r_p = recorded(d, d.C), recorded(d, d.P)
    rise = xr(s_c["cl"] - s_c["cur"] - r_c["cl"])
    wc_fall = xr((r_c["ca"] - r_c["cl"]) - s_c["wc"])
    under_p = xr(s_p["cl"] - s_p["cur"] - r_p["cl"])
    claim(rise > 0 and wc_fall > 0, "current liabilities rise and working capital falls")
    claim(under_p > mat_p or pay_p["total"] > mat_p,
          f"at {d.P} current liabilities, or the payroll liability alone, were understated by more than {d.P} materiality")
    claim(all(adj["pay"][y]["total"] > 0 for y in d.years) and d.one(
        "SELECT COUNT(*) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'JournalEntry' AND VoucherNumber <> ?",
        d.account("2030"), opening_entry(d)) == 0, "the missing payroll accrual recurs every year")
    # P1 and P2 are estimates: each is measured at the year-end and, net of the same estimate at the end of d.P (which
    # reverses in d.C), on d.C income
    p1 = -allowance(d)
    claim(abs(allowance_at(d, d.C) - allowance(d)) < 0.005, "the allowance at the end of each year is measured as Exercise 8.1 measures it")
    p1_prior = -allowance_at(d, d.P)
    ra = returns_across(d)
    claim(sorted(ra["pairs"]) == [(d.P, d.F), (d.C, d.P)], "every return in a later year is returned the year after its delivery")
    rc, rp = ra["by_year"].get(d.C, dict(n=0, rev=0.0, cost=0.0)), ra["by_year"].get(d.P, dict(n=0, rev=0.0, cost=0.0))
    p2 = xr(-(rc["rev"] - rc["cost"]))
    p2_prior = xr(-(rp["rev"] - rp["cost"]))
    marks = ",".join("?" * len(WRITE_DOWN))
    by_year = dict(d.q(f"SELECT CAST(substr(sr.ReturnDate, 1, 4) AS INTEGER), SUM(srl.ExtendedStandardCost) FROM SalesReturn sr "
                       f"JOIN SalesReturnLine srl ON srl.SalesReturnID = sr.SalesReturnID WHERE sr.ReasonCode IN ({marks}) "
                       f"GROUP BY 1", *WRITE_DOWN))
    restocked = dict(d.q("SELECT CAST(substr(sr.ReturnDate, 1, 4) AS INTEGER), SUM(srl.ExtendedStandardCost) FROM SalesReturn sr "
                         "JOIN SalesReturnLine srl ON srl.SalesReturnID = sr.SalesReturnID GROUP BY 1"))
    to_stock = dict(d.q("SELECT FiscalYear, SUM(Debit) FROM GLEntry WHERE AccountID = ? AND SourceDocumentType = 'SalesReturn' "
                        "GROUP BY 1", d.account("1040")))
    claim(all(abs(restocked.get(y, 0.0) - to_stock.get(y, 0.0)) < 0.005 for y in d.years),
          "returns are restocked at their full standard cost")
    p3_years = [xr(by_year.get(y, 0.0)) for y in d.years]
    p3 = -p3_years[-1]
    aggregate = xr(p1 + p2 + p3)
    agg_income = xr((p1 - p1_prior) + (p2 - p2_prior) + p3)
    claim(-aggregate < mat_c and abs(agg_income) < mat_c, "the passed items are below materiality, at the year-end and on income")
    residual = composition(d, d.C)["excess"]
    claim(residual < TRIVIAL * mat_c, "the freight residual is trivial")
    return dict(a=a, total=total, split_p=split[d.P], split_c=split[d.C], a2_accounts=a2_accounts, entries=entries,
                equity_p=adj["equity"][d.P], equity_c=adj["equity"][d.C], adj_ni_p=adj["adj_ni"][d.P], adj_ni_c=adj["adj_ni"][d.C],
                ni_c=net_income(d, d.C), pay_p=pay_p, pay_c=pay_c, cut_p=adj["cut"][d.P], cut_c=adj["cut"][d.C],
                old_p=adj["old"][d.P], old_c=adj["old"][d.C], intr_p=adj["intr"][d.P], intr_c=adj["intr"][d.C],
                cur_p=current_portion(d, d.P), cur_c=current_portion(d, d.C), c1090_p=c1090[d.P], c1090_c=c1090[d.C],
                wip_p=xr(bal(d, ["1046"], ye(d.P))), wip_c=xr(bal(d, ["1046"], ye(d.C))), mat_c=mat_c, mat_p=mat_p,
                share=total["C"] / mat_c, rise=rise, wc_fall=wc_fall, under_p=under_p, p1=p1, p1_prior=p1_prior,
                p1_income=xr(p1 - p1_prior),
                p2=dict(n=rc["n"], rev=rc["rev"], cost=rc["cost"], n_prior=rp["n"], rev_prior=rp["rev"], cost_prior=rp["cost"],
                        effect=p2, income=xr(p2 - p2_prior)),
                p3=dict(effect=p3, total=xr(sum(p3_years)), years=p3_years), aggregate=aggregate, agg_income=agg_income,
                agg_share=-aggregate / mat_c, residual=residual)


# --- Requirement 6 -------------------------------------------------------------------------------------------

@note("ch17.r6", CHAPTER)
def r6(d, claim):
    adj = adjustments(d)
    s_c, s_p = statement(d, d.C), statement(d, d.P)
    for y, s in ((d.C, s_c), (d.P, s_p)):
        claim(abs(s["ta"] - (recorded(d, y)["ta"] + adj["cut"][y])) < 0.005,
              f"adjusted total assets at {y} are the recorded ones plus the revenue cutoff")
        claim(abs(s["tl"] + s["equity"] - s["ta"]) < 0.005, f"the adjusted balance sheet at {y} balances")
        t = tb(d, ye(y))
        covered = set(CASH + RECEIVABLES + INVENTORIES + PREPAID + PAYABLES + ["2020"] + PAYROLL + COMMISSIONS + ACCRUED
                      + SALES_TAX + CREDITS)
        claim(all(abs(v) < 0.005 for n, v in t.items() if chart(d)[n]["sub"] in ("Current Asset", "Contra Current Asset",
                                                                                 "Current Liability") and n not in covered),
              f"the statement's lines hold every current account with a balance at {y}")
    i_p, i_c = adjusted_income(d, d.P), adjusted_income(d, d.C)
    claim(abs(i_p["ni"] - adj["adj_ni"][d.P]) < 0.005 and abs(i_c["ni"] - adj["adj_ni"][d.C]) < 0.005,
          "the adjusted income statements end at the adjusted net income")
    reported = xr(recorded(d, d.F)["re"] + net_income(d, d.F))
    claim(abs(reported - recorded(d, d.P)["re"]) < 0.005, "retained earnings as previously reported are the ledger's")
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", d.account("3040")) == 0, "no distributions")
    cf_c, cf_p = cash_flows(d, d.C), cash_flows(d, d.P)
    for y, cf in ((d.C, cf_c), (d.P, cf_p)):
        claim(abs(cf["operating"] - cf["recorded_operating"]) < 0.005,
              f"the adjustments leave {y}'s operating cash flow as the recorded ledger gives it")
        claim(abs(cf["operating"] + cf["investing"] + cf["financing"] - cf["cash"]) < 0.005,
              f"the sections of {y} add up to the change in cash")
        claim(abs(cf["dep"] - cf["depreciation_entries"]) < 0.005, f"{y}'s depreciation is the depreciation entries'")
    claim(no_tax_account(d), "no income tax is recorded")
    claim(cf_p["notes_financed"] == 0 and cf_c["notes_financed"] > 0, f"equipment was financed by a note only in {d.C}")
    return dict(s_c=s_c, s_p=s_p, i_p=i_p, i_c=i_c, reported=reported, correction=adj["total"]["re"],
                restated=xr(reported + adj["total"]["re"]), cf_c=cf_c, cf_p=cf_p)


# --- Requirement 7 -------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def register(d) -> list[dict]:
    return [dict(code=c, account=str(a), contra=str(ad), service=s, life=life, cost=cost, disposal=disp, residual=res)
            for c, a, ad, s, life, cost, disp, res in d.q(
                "SELECT f.AssetCode, a.AccountNumber, ad.AccountNumber, f.InServiceDate, f.UsefulLifeMonths, f.OriginalCost, "
                "f.DisposalDate, f.ResidualValue FROM FixedAsset f JOIN Account a ON a.AccountID = f.AssetAccountID "
                "JOIN Account ad ON ad.AccountID = f.AccumulatedDepreciationAccountID ORDER BY f.AssetCode")]


def month_index(day: str) -> int:
    return int(day[:4]) * 12 + int(day[5:7]) - 1


def schedule(d, contra: str, year: int) -> float:
    """The register's depreciation of a class in a fiscal year: each asset's cost over its life, rounded to the cent a
    month, from the month after it is placed in service through the month before disposal."""
    total = 0.0
    for a in register(d):
        if a["contra"] != contra:
            continue
        first, last = month_index(a["service"]) + 1, month_index(a["service"]) + a["life"]
        if a["disposal"]:
            last = min(last, month_index(a["disposal"]) - 1)
        months = sum(1 for m in range(first, last + 1) if m // 12 == year)
        total += months * xr(a["cost"] / a["life"])
    return total


def depreciation_by_contra(d, contra: str, year: int) -> float:
    return d.one("SELECT COALESCE(SUM(g.Credit - g.Debit), 0) FROM GLEntry g JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
                 "AND g.SourceDocumentType = 'JournalEntry' WHERE j.EntryType = 'Depreciation' AND g.AccountID = ? "
                 "AND g.FiscalYear = ?", d.account(contra), year)


def depreciation_debits(d, number: str, year: int) -> float:
    return d.one("SELECT COALESCE(SUM(g.Debit), 0) FROM GLEntry g JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber "
                 "AND g.SourceDocumentType = 'JournalEntry' WHERE j.EntryType = 'Depreciation' AND g.AccountID = ? "
                 "AND g.FiscalYear = ?", d.account(number), year)


def additions(d, year: int) -> dict:
    rows = [a for a in register(d) if a["service"][:4] == str(year)]
    groups = defaultdict(lambda: dict(cost=0.0, codes=[]))
    for a in rows:
        groups[a["account"]]["cost"] += a["cost"]
        groups[a["account"]]["codes"].append(a["code"])
    return dict(total=sum(a["cost"] for a in rows), codes=[a["code"] for a in rows],
                groups=[dict(account=k, cost=v["cost"], codes=v["codes"]) for k, v in sorted(groups.items())])


def disposal(d, year: int, claim) -> dict:
    assets = [a for a in register(d) if a["disposal"] and a["disposal"][:4] == str(year)]
    entries = disposals(d, year)
    claim(len(assets) == 1 and len(entries) == 1, f"one asset was disposed of in {year}, by one entry")
    if not assets or not entries:
        return dict(code="?", cost=0.0, written=0.0, proceeds=0.0, loss=0.0)
    e = entries[0]
    claim(abs(e["cost"] - assets[0]["cost"]) < 0.005, f"the {year} disposal entry removes the asset's cost")
    return dict(code=assets[0]["code"], cost=e["cost"], written=e["written"], proceeds=e["proceeds"], loss=e["loss"])


@note("ch17.r7", CHAPTER)
def r7(d, claim):
    F, P, C = d.F, d.P, d.C
    fixed = accounts_of(d, "Fixed Asset")
    contra = accounts_of(d, "Contra Fixed Asset")
    cost = {y: xr(bal(d, fixed, ye(y))) for y in (F, P, C)}
    acc = {y: xr(-bal(d, contra, ye(y))) for y in (F, P, C)}
    add_p, add_c = additions(d, P), additions(d, C)
    disp_p, disp_c = disposal(d, P, claim), disposal(d, C, claim)
    claim(abs(cost[F] + add_p["total"] - disp_p["cost"] - cost[P]) < 0.005
          and abs(cost[P] + add_c["total"] - disp_c["cost"] - cost[C]) < 0.005, "the cost rolls forward through the register")
    claim(disp_p["proceeds"] > 0 and disp_c["proceeds"] == 0, f"the {P} disposal had proceeds and the {C} one none")
    claim(len(add_c["codes"]) == 1, f"one addition in {C}")
    financing = dict(d.q("SELECT f.AssetCode, e.FinancingType FROM FixedAssetEvent e JOIN FixedAsset f ON f.FixedAssetID = "
                         "e.FixedAssetID WHERE e.EventType IN ('Acquisition', 'Improvement')"))
    claim(all(financing.get(c) == "Note" for c in add_c["codes"]), f"the {C} addition was financed by a note")
    classes = [dict(name=CLASSES[k], p=xr(depreciation_by_contra(d, k, P)), c=xr(depreciation_by_contra(d, k, C)))
               for k in sorted(CLASSES)]
    claim(set(CLASSES) == set(contra), "the classes are the accumulated depreciation accounts")
    dep = {y: xr(sum(depreciation_by_contra(d, k, y) for k in contra)) for y in (P, C)}
    to6130 = {y: xr(depreciation_debits(d, "6130", y)) for y in (P, C)}
    to1090 = {y: xr(depreciation_debits(d, "1090", y)) for y in (P, C)}
    claim(all(abs(dep[y] - to6130[y] - to1090[y]) < 0.005 for y in (P, C)), "depreciation goes to 6130 and 1090 only")
    nbv = [xr(bal(d, [a, b], ye(C))) for a, b in PAIRS]
    claim(sorted(a for a, _ in PAIRS) == sorted(n for n in fixed if n in tb(d, ye(C))), "the classes cover the asset accounts in use")
    lives = [a["life"] for a in register(d)]
    claim(all(a["residual"] == 0 for a in register(d)), "no asset has a residual value")
    claim(all(abs(schedule(d, k, y) - depreciation_by_contra(d, k, y)) < 0.005 for k in contra for y in d.years),
          "the register, at monthly amounts rounded to the cent, reproduces the ledger")
    notes_ = []
    for n in notes_payable(d):
        notes_.append(dict(principal=n["principal"], rate=f"{n['rate'] * 100:g}%", term=n["term"], payment=n["payment"],
                           start=f"{month_of(n['start'])} {n['start'][:4]}", asset=n["asset"], c=outstanding(n, ye(C)),
                           p=outstanding(n, ye(P)) if n["origin"] <= ye(P) else None))
    notes_total = xr(sum(n["c"] for n in notes_))
    claim(abs(notes_total + bal(d, ["2110"], ye(C))) < 0.005, "the schedules' balances equal 2110")
    claim(all(n["asset"] for n in notes_payable(d)), "each note is linked to the asset it financed")
    columns = [r[1].lower() for r in d.q("PRAGMA table_info(DebtAgreement)")]
    claim(not any("collateral" in c or "secur" in c or "lien" in c for c in columns), "the records show no security interest")
    maturities = defaultdict(float)
    for n in notes_payable(d):
        for line in n["lines"]:
            if line["date"] > ye(C):
                maturities[int(line["date"][:4])] += line["principal"]
    # revenue on the adjusted basis
    accounts = revenue_accounts(d)
    services = [g for g in accounts if g not in GROUP_ORDER]
    claim(services == ["Services"] and "Design Services" in chart(d)[accounts["Services"]]["name"],
          "the one other item group is the design services, on their own account")
    freight = freight_account(d)
    claim(len(freight) == 1 and "Freight" in chart(d)[freight[0]]["name"], "freight billed goes to one freight revenue account")
    adj_group = {P: defaultdict(float), C: defaultdict(float)}
    adj_segment = {P: defaultdict(float), C: defaultdict(float)}
    for y in (P, C):
        for g, v in cutoff(d, y)["group"].items():
            adj_group[y][g] += v
        for g, v in cutoff(d, y - 1)["group"].items():
            adj_group[y][g] -= v
        for s, v in cutoff(d, y)["segment"].items():
            adj_segment[y][s] += v
        for s, v in cutoff(d, y - 1)["segment"].items():
            adj_segment[y][s] -= v
    revenue = {y: {g: xr(-activity(d, [accounts[g]], y) + adj_group[y].get(g, 0.0)) for g in accounts} for y in (P, C)}
    freight_rev = {y: xr(-activity(d, freight, y)) for y in (P, C)}
    lines = ("FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID JOIN Customer c "
             "ON c.CustomerID = si.CustomerID JOIN (SELECT SourceDocumentID AS id, MIN(PostingDate) AS pd FROM GLEntry "
             "WHERE SourceDocumentType = 'SalesInvoice' GROUP BY 1) p ON p.id = si.SalesInvoiceID")
    by_posting = {(int(y), g): v for y, g, v in d.q(f"SELECT substr(p.pd, 1, 4), i.ItemGroup, SUM(sil.LineTotal) {lines} "
                                                     f"JOIN Item i ON i.ItemID = sil.ItemID GROUP BY 1, 2")}
    claim(all(abs(by_posting.get((y, g), 0.0) + activity(d, [accounts[g]], y)) < 0.005 for y in (P, C) for g in accounts),
          "the ledger's revenue by account is the invoice lines by posting year")
    segment = {y: {s: xr(v + adj_segment[y].get(s, 0.0)) for s, v in d.q(
        f"SELECT c.CustomerSegment, SUM(sil.LineTotal) {lines} WHERE substr(p.pd, 1, 4) = ? GROUP BY 1", str(y))} for y in (P, C)}
    for y in (P, C):
        for s, v in adj_segment[y].items():
            segment[y].setdefault(s, xr(v))
    groups = ordered_groups([g for g in accounts if g in GROUP_ORDER])
    product = {y: xr(sum(revenue[y][g] for g in groups)) for y in (P, C)}
    services_rev = {y: revenue[y]["Services"] if "Services" in revenue[y] else 0.0 for y in (P, C)}
    ship = {int(y): v for y, v in d.q("SELECT substr(s.ShipmentDate, 1, 4), SUM(sil.LineTotal) FROM SalesInvoiceLine sil "
                                      "JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s "
                                      "ON s.ShipmentID = sl.ShipmentID GROUP BY 1")}
    unbilled_c = cutoff(d, C)["total"]
    diff = {P: xr(product[P] - ship.get(P, 0.0)), C: xr(product[C] - ship.get(C, 0.0) - unbilled_c)}
    # what makes the adjusted revenue differ from the revenue by ship date: invoice lines that Requirement 4's test, which
    # dates each late invoice by its latest delivery, counts in another year than their own delivery
    assigned = {i["id"]: i["year"] for i in late(d)}
    moved, mixed, single = defaultdict(float), set(), set()
    for sid, number, total, delivered, posted, years in d.q(
            "SELECT si.SalesInvoiceID, si.InvoiceNumber, sil.LineTotal, CAST(substr(s.DeliveryDate, 1, 4) AS INTEGER), "
            "CAST(substr(p.pd, 1, 4) AS INTEGER), n.years FROM SalesInvoiceLine sil JOIN SalesInvoice si ON si.SalesInvoiceID = "
            "sil.SalesInvoiceID JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = "
            "sl.ShipmentID JOIN (SELECT SourceDocumentID AS id, MIN(PostingDate) AS pd FROM GLEntry WHERE SourceDocumentType = "
            "'SalesInvoice' GROUP BY 1) p ON p.id = si.SalesInvoiceID JOIN (SELECT sil2.SalesInvoiceID AS id, COUNT(DISTINCT "
            "substr(s2.DeliveryDate, 1, 4)) AS years FROM SalesInvoiceLine sil2 JOIN ShipmentLine sl2 ON sl2.ShipmentLineID = "
            "sil2.ShipmentLineID JOIN Shipment s2 ON s2.ShipmentID = sl2.ShipmentID GROUP BY 1) n ON n.id = si.SalesInvoiceID"):
        year = assigned.get(sid, posted)
        if year != delivered:
            moved[year] += total
            moved[delivered] -= total
            (mixed if years > 1 else single).add(number)
    claim(all(abs(diff[y] - moved.get(y, 0.0)) < 0.005 for y in (P, C)),
          "the adjusted product revenue differs from the revenue by ship date only by lines counted in another year")
    claim(not single, "the lines counted in another year belong to invoices that bill deliveries of two years")
    # contract balances
    claim(d.one("SELECT COUNT(*) FROM GLEntry WHERE AccountID = ?", d.account("2070")) == 0, "2070 is unused")
    issued = d.q("SELECT COUNT(*), COALESCE(SUM(GrandTotal), 0) FROM CreditMemo WHERE Status = 'Issued'")[0]
    credits = [xr(-bal(d, CREDITS, ye(y))) for y in (F, P, C)]
    claim(abs(issued[1] - credits[-1]) < 0.005, f"the Issued credit memos are the balance of 2060 at {C}")
    # services
    billable = d.one("SELECT SUM(BillableHours) FROM ServiceTimeEntry")
    billed = d.one("SELECT SUM(BilledHours) FROM ServiceBillingLine")
    claim(abs(billable - billed) < 0.005, "every billable hour is billed")
    claim(d.one("SELECT COUNT(*) FROM ServiceBillingLine b JOIN SalesInvoiceLine sil ON sil.SalesInvoiceLineID = b.SalesInvoiceLineID "
                "JOIN SalesInvoice si ON si.SalesInvoiceID = sil.SalesInvoiceID WHERE substr(b.BillingPeriodEndDate, 1, 7) = ? "
                "AND si.InvoiceDate <> ?", f"{C}-12", ye(C)) == 0
          and d.one("SELECT MAX(WorkDate) FROM ServiceTimeEntry") <= ye(C), "December's work was billed on 31 December")
    # the engagements not Billed by status: each must have billed every hour worked, so there is no unbilled work
    engs = []
    for eid, status, end, planned in d.q("SELECT ServiceEngagementID, Status, EndDate, PlannedHours FROM ServiceEngagement "
                                         "WHERE Status <> 'Billed' ORDER BY 1"):
        worked, through = d.q("SELECT COALESCE(SUM(BillableHours), 0), MAX(WorkDate) FROM ServiceTimeEntry "
                              "WHERE ServiceEngagementID = ?", eid)[0]
        e_billed = d.one("SELECT COALESCE(SUM(BilledHours), 0) FROM ServiceBillingLine WHERE ServiceEngagementID = ?", eid)
        claim(abs(worked - e_billed) < 0.005, f"engagement {eid} billed all its hours")
        engs.append(dict(id=eid, status=status, end=end or "?", ended=end is not None and end <= ye(C), billed=e_billed,
                         through=day_month(through) if through else "?", planned=planned or 0.0,
                         short=(planned or 0.0) > worked + 0.005))
    # inventories and accrued liabilities
    claim(chart(d)["5060"]["sub"] == "COGS", "the purchase price variance goes to cost of goods sold")
    claim(d.one("SELECT COUNT(*) FROM GoodsReceiptLine grl JOIN PurchaseOrderLine pol ON pol.POLineID = grl.POLineID "
                "WHERE ABS(grl.ExtendedStandardCost - ROUND(grl.QuantityReceived * pol.UnitCost, 2)) > 0.011") == 0,
          "materials are received at purchase-order cost")
    claim(d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Item i ON i.ItemID = sl.ItemID "
                "WHERE ABS(sl.ExtendedStandardCost - ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011") == 0,
          "finished goods leave inventory at standard cost")
    s_c, s_p = statement(d, C), statement(d, P)
    opening_2030 = opening_line(d, "2030")
    # withholdings and benefits of the last payroll not yet remitted at the year-end (2031-2033)
    withheld = {y: xr(-bal(d, PAYROLL[1:], ye(y))) for y in (P, C)}
    claim(all(abs(s["payroll"] - adjustments(d)["pay"][y]["total"] - opening_2030 - withheld[y]) < 0.005
              and abs(-bal(d, ["2030"], ye(y)) - opening_2030) < 0.005 for y, s in ((C, s_c), (P, s_p))),
          "payroll and related is the accrual plus the opening line plus the payroll liabilities not yet remitted")
    return dict(cost_f=cost[F], cost_p=cost[P], cost_c=cost[C], add_p=add_p, add_c=add_c, disp_p=disp_p, disp_c=disp_c,
                classes=classes, dep_p=dep[P], dep_c=dep[C], to6130_p=to6130[P], to6130_c=to6130[C], to1090_p=to1090[P],
                to1090_c=to1090[C], acc_f=acc[F], acc_p=acc[P], acc_c=acc[C], nbv=nbv, life_low=min(lives), life_high=max(lives),
                notes=notes_, notes_total=notes_total, maturities=[(y, xr(v)) for y, v in sorted(maturities.items())],
                revenue=[dict(label=g, c=revenue[C][g], p=revenue[P][g]) for g in groups],
                svc_c=services_rev[C], svc_p=services_rev[P], fr_c=freight_rev[C], fr_p=freight_rev[P],
                segments=[dict(name=k, c=v, p=segment[P].get(k, 0.0)) for k, v in sorted(segment[C].items(), key=lambda kv: -kv[1])],
                point_c=xr(product[C] + freight_rev[C]), point_p=xr(product[P] + freight_rev[P]), product_p=product[P],
                ship_c=xr(ship.get(C, 0.0)), ship_p=xr(ship.get(P, 0.0)), unbilled=unbilled_c, diff_p=diff[P], diff_c=diff[C],
                mixed=sorted(mixed),
                recv_f=statement(d, F)["recv"], recv_p=s_p["recv"], recv_c=s_c["recv"], opening_ar=opening_line(d, "1020"),
                credits=credits, issued=word(issued[0]), issued_n=issued[0], billable=billable, engs=engs,
                s_c=s_c, s_p=s_p, opening_2030=opening_2030, w_c=withheld[C], w_p=withheld[P])


# --- Requirement 8 -------------------------------------------------------------------------------------------

@note("ch17.r8", CHAPTER)
def r8(d, claim):
    after = ye(d.C)
    rows = d.q("SELECT SourceDocumentType, COUNT(*), MIN(PostingDate), MAX(PostingDate) FROM GLEntry WHERE PostingDate > ? GROUP BY 1",
               after)
    claim([r[0] for r in rows] == ["DisbursementPayment"], f"the {d.N} records are supplier payments only")
    sides = d.q("SELECT a.AccountNumber, SUM(g.Debit > 0), SUM(g.Credit > 0) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                "WHERE g.PostingDate > ? GROUP BY 1 ORDER BY 1", after)
    claim([(str(n), dr > 0, cr > 0) for n, dr, cr in sides] == [("1010", False, True), ("2010", True, False)],
          "every row debits 2010 or credits 1010")
    n_pay, paid, first, last = d.q("SELECT COUNT(*), SUM(Amount), MIN(PaymentDate), MAX(PaymentDate) FROM DisbursementPayment "
                                   "WHERE PaymentDate > ?", after)[0]
    n_rows = sum(r[1] for r in rows)
    claim(n_rows == 2 * n_pay, "two ledger rows per payment")
    invoices = d.q("SELECT pi.PurchaseInvoiceID, pi.ReceivedDate, pi.GrandTotal, SUM(dp.Amount), pi.SupplierID FROM DisbursementPayment dp "
                   "JOIN PurchaseInvoice pi ON pi.PurchaseInvoiceID = dp.PurchaseInvoiceID WHERE dp.PaymentDate > ? GROUP BY 1", after)
    received = sorted(r[1] for r in invoices)
    claim(received[-1] <= after and received[0][:4] == str(d.C), f"all were received in {d.C} and recorded in payables by the year-end")
    claim(d.one("SELECT COUNT(*) FROM PurchaseInvoice WHERE ReceivedDate > ?", after) == 0, f"no invoice was received after {d.C}")
    same_end = f"{d.C}-{last[5:]}"
    same_n, same_amount = d.q("SELECT COUNT(*), SUM(Amount) FROM DisbursementPayment WHERE PaymentDate BETWEEN ? AND ?",
                              f"{d.C}-01-01", same_end)[0]
    m1, m2 = int(first[5:7]), int(last[5:7])
    due_end = f"{d.N}-{m2:02d}-{calendar.monthrange(d.N, m2)[1]:02d}"
    due = d.one("SELECT SUM(pi.GrandTotal - COALESCE((SELECT SUM(dp.Amount) FROM DisbursementPayment dp WHERE dp.PurchaseInvoiceID = "
                "pi.PurchaseInvoiceID AND dp.PaymentDate <= ?1), 0)) FROM PurchaseInvoice pi WHERE pi.ReceivedDate <= ?1 "
                "AND pi.DueDate BETWEEN ?2 AND ?3", after, f"{d.N}-{m1:02d}-01", due_end)
    periods = d.q("SELECT PayrollPeriodID, PayDate FROM PayrollPeriod WHERE PayDate BETWEEN ? AND ? ORDER BY PayDate",
                  f"{d.N}-01-01", last)
    claim(len(periods) == 2, "two pay dates fall in the extract")
    claim(all(d.one("SELECT COUNT(*) FROM PayrollRegister WHERE PayrollPeriodID = ?", p[0]) == 0 for p in periods),
          "the extract has no payroll for them")
    due_notes = d.q("SELECT PaymentDate, Status, JournalEntryID FROM DebtScheduleLine WHERE PaymentDate BETWEEN ? AND ? ORDER BY 1",
                    f"{d.N}-01-01", last)
    claim(due_notes and all(s == "Scheduled" and je is None for _, s, je in due_notes), "the note payments due are all Scheduled")
    s_c, s_p = statement(d, d.C), statement(d, d.P)
    cf_c, cf_p = cash_flows(d, d.C), cash_flows(d, d.P)
    claim(s_c["qr"] < s_p["qr"], "the quick ratio fell")
    issues = materials_issues(d, d.C)
    claim(s_c["mat"] > issues, "materials exceed twelve months of issues")
    claim(adjustments(d)["adj_ni"][d.C] > 0, "the company is profitable")
    claim_opening(d, claim)
    return dict(n_pay=n_pay, paid=xr(paid), first_day=day_month(first), last_day=day_month(last), rows=n_rows,
                n_inv=len(invoices), n_sup=len({r[4] for r in invoices}), recv_first=month_of(received[0]),
                recv_last=month_of(received[-1]), full=sum(1 for r in invoices if abs(r[2] - r[3]) < 0.005),
                same_n=same_n, same_amount=xr(same_amount), due_months=f"{MONTHS[m1 - 1]} and {MONTHS[m2 - 1]}", due=xr(due),
                periods=[p[0] for p in periods], pay_dates=[p[1] for p in periods], note_dates=short_series([r[0] for r in due_notes]),
                cash_net=s_c["cash_net"], qr_c=s_c["qr"], qr_p=s_p["qr"], op_c=cf_c["operating"], op_p=cf_p["operating"],
                inv_share=s_c["inv"] / s_c["ca"], mat=s_c["mat"], issues=xr(issues), opening_ap=opening_line(d, "2010"),
                years=word(len(d.years)), wc_m=f"{s_c['wc'] / 1e6:.1f}", debt=s_c["notes"])


# --- Requirement 9 -------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def revaluation(d) -> dict[int, float]:
    """The manufactured finished goods on hand at each year-end revalued from their standard conversion cost to a
    standard rebuilt on normal capacity: the Part III plan's rate with burden at its hours per standard hour, the factory
    overhead entries, the salaried staff with burden, and the next year's depreciation over the plan's standard hours."""
    std = completions(d)["std"]
    b = burden(d, d.C)
    labor = round(rate(d, d.C), 2) * (1 + b)
    plan = round(yearly(d)[0]["ratio"], 2)
    foh = d.one("SELECT SUM(g.Debit) FROM GLEntry g JOIN JournalEntry j ON j.JournalEntryID = g.SourceDocumentID "
                "WHERE g.SourceDocumentType = 'JournalEntry' AND j.EntryType = 'Factory Overhead' AND g.AccountID = ? "
                "AND g.FiscalYear = ?", d.account("1090"), d.C)
    salary = d.one("SELECT SUM(pr.GrossPay) FROM PayrollRegister pr JOIN PayrollPeriod pp ON pp.PayrollPeriodID = pr.PayrollPeriodID "
                   "JOIN Employee e ON e.EmployeeID = pr.EmployeeID JOIN CostCenter c ON c.CostCenterID = pr.CostCenterID "
                   "WHERE c.CostCenterName = 'Manufacturing' AND e.PayClass = 'Salary' AND pp.FiscalYear = ?", d.C)
    dep_next = round(sum(plant_depreciation(d)["months"][d.N]), 2)
    new = labor * plan + foh / std + salary * (1 + b) / std + dep_next / std
    items = {i: (h or 0.0, conv or 0.0, mode) for i, h, conv, mode in d.q(
        "SELECT ItemID, StandardLaborHoursPerUnit, StandardConversionCost, SupplyMode FROM Item")}
    out = {}
    for y in d.years:
        end, net = ye(y), defaultdict(float)
        for i, qty in d.q("SELECT pcl.ItemID, SUM(pcl.QuantityCompleted) FROM ProductionCompletionLine pcl JOIN ProductionCompletion pc "
                          "ON pc.ProductionCompletionID = pcl.ProductionCompletionID WHERE pc.CompletionDate <= ? GROUP BY 1", end):
            net[i] += qty
        for i, qty in d.q("SELECT sl.ItemID, SUM(sl.QuantityShipped) FROM ShipmentLine sl JOIN Shipment s ON s.ShipmentID = "
                          "sl.ShipmentID WHERE s.ShipmentDate <= ? GROUP BY 1", end):
            net[i] -= qty
        for i, qty in d.q("SELECT srl.ItemID, SUM(srl.QuantityReturned) FROM SalesReturnLine srl JOIN SalesReturn sr "
                          "ON sr.SalesReturnID = srl.SalesReturnID WHERE sr.ReturnDate <= ? GROUP BY 1", end):
            net[i] += qty
        on_hand = {i: u for i, u in net.items() if items[i][2] == "Manufactured" and u > 0}
        out[y] = sum(u * (items[i][0] * new - items[i][1]) for i, u in on_hand.items())
    return out


@note("ch17.r9", CHAPTER)
def r9(d, claim):
    claim(no_tax_account(d), "no tax account and no tax recorded")
    equity_used = {str(n) for (n,) in d.q("SELECT DISTINCT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                                          "WHERE a.AccountType = 'Equity' AND a.AccountSubType NOT IN ('Closing', 'Header')")}
    claim(equity_used == {"3010", "3030"}, "equity is common stock and retained earnings, with no distributions")
    adj_ni = adjustments(d)["adj_ni"][d.C]
    provision = round(adj_ni * FEDERAL, -4)
    claim(adj_ni * FEDERAL > 3 * materiality(d, d.C), "the omitted provision is several times materiality")
    rent_rows = d.q("SELECT j.PostingDate, a.AccountNumber, SUM(g.Debit), SUM(g.Credit) FROM JournalEntry j JOIN GLEntry g "
                    "ON g.SourceDocumentType = 'JournalEntry' AND g.SourceDocumentID = j.JournalEntryID JOIN Account a "
                    "ON a.AccountID = g.AccountID WHERE j.EntryType = 'Rent' GROUP BY 1, 2")
    claim(all(day == first_weekday(day) for day, *_ in rent_rows), "rent is paid on the first weekday of each month")
    claim({str(n) for _, n, dr, cr in rent_rows if cr > 0} == {"1010"}, "rent is paid straight from cash")
    debited = {str(n) for _, n, dr, cr in rent_rows if dr > 0}
    claim(len(debited) == 2 and all("Rent" in chart(d)[n]["name"] for n in debited)
          and {chart(d)[n]["name"].split(" - ")[-1] for n in debited} == {"Office", "Warehouse"}, "the rent is for the office and the warehouse")
    monthly = defaultdict(float)
    for day, n, dr, cr in rent_rows:
        monthly[day[:7]] += dr
    series = [monthly[m] for m in sorted(monthly)]
    claim(len(set(round(v, 2) for v in series)) > 1 and all(abs(b / a - 1) < 0.05 for a, b in zip(series, series[1:])),
          "the amounts vary slightly from month to month (within 5% of the month before)")
    rent = [xr(sum(v for m, v in monthly.items() if m[:4] == str(y))) for y in d.years]
    unused = {n for n, _, _ in never_posted(d)}
    claim({"2120", "1140", "7010"} <= unused, "2120, 1140, and 7010 are unused")
    categories = [c.lower() for (c,) in d.q("SELECT DISTINCT SupplierCategory FROM Supplier")]
    names = [n.lower() for (n,) in d.q("SELECT SupplierName FROM Supplier")]
    landlord = ("real estate", "property", "properties", "realty", "leasing", "landlord", "rental")
    claim(not any(w in x for x in categories + names for w in landlord), "no lessor appears among the suppliers")
    a2050 = d.account("2050")
    sides = d.q("SELECT SourceDocumentType, SUM(Debit), SUM(Credit) FROM GLEntry WHERE AccountID = ? AND PostingDate <= ? GROUP BY 1",
                a2050, ye(d.C))
    claim({s for s, dr, cr in sides if cr > 0} == {"SalesInvoice"} and {s for s, dr, cr in sides if dr > 0} == {"CreditMemo"},
          "2050 credits only from invoices, debits only from credit memos")
    memo_debits = xr(sum(dr for s, dr, cr in sides if s == "CreditMemo"))
    stax = xr(-bal(d, SALES_TAX, ye(d.C)))
    claim_opening(d, claim)
    o = dict(ar=opening_line(d, "1020"), prepaid=opening_line(d, "1050"), ap=opening_line(d, "2010"),
             payroll=opening_line(d, "2030"), accrued=opening_line(d, "2040"))
    assets, liabilities = xr(o["ar"] + o["prepaid"]), xr(o["ap"] + o["payroll"] + o["accrued"])
    tables = [t.lower() for (t,) in d.q("SELECT name FROM sqlite_master WHERE type = 'table'")]
    claim(not any("bank" in t or "reconcil" in t for t in tables), "no bank reconciliation in the records")
    claim(not any(w in t for t in tables for w in ("opening", "stock", "onhand", "inventorybalance", "inventorycount")),
          "the opening inventory has no item detail")
    claim(d.one("SELECT COUNT(*) FROM ShipmentLine sl JOIN Item i ON i.ItemID = sl.ItemID "
                "WHERE ABS(sl.ExtendedStandardCost - ROUND(sl.QuantityShipped * i.StandardCost, 2)) > 0.011") == 0,
          f"the standards are unchanged since {d.F}")
    reval = revaluation(d)
    claim(reval[d.C] > 0 and reval[d.P] > 0, "the finished goods would be higher at a standard rebuilt on normal capacity")
    return dict(years=word(len(d.years)), adj_ni=adj_ni, provision=provision, rent=rent, stax=stax, memo_debits=memo_debits,
                o=o, equity=xr(liabilities - assets), assets=assets, liabilities=liabilities,
                reval_c=round(reval[d.C], -3), reval_p=round(reval[d.P], -3))
