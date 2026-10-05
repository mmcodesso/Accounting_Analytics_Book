"""Chapter 14's instructor notes: the values each note states, and the claims its wording makes.

The DAX results of the chapter are reproduced with SQL twins of its model: the invoice lines with the invoice date,
number and customer merged in (Tutorial 14.1); ListAmount = Quantity x BaseListPrice, DiscountAmount = Quantity x
UnitPrice x Discount and standard cost Quantity x Item.StandardCost, all unrounded (Tutorials 13.1 and 14.2); the
Date table one row per day from the first fiscal year to the year after the current one; and the ledger with the
year-end closing entries flagged through JournalEntry.EntryType (Tutorial 14.3).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from notes import note

T1 = "chapters/14-data-models-and-dax/_tutorial-01.qmd"
T2 = "chapters/14-data-models-and-dax/_tutorial-02.qmd"
T3 = "chapters/14-data-models-and-dax/_tutorial-03.qmd"
EXERCISES = "chapters/14-data-models-and-dax/_exercises.qmd"
MCQ = "chapters/14-data-models-and-dax/_multiple-choice.qmd"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
# Exercise 14.6's revenue accounts: the item groups' revenue lines (the exercise names them).
REVENUE = ["4010", "4020", "4030", "4040", "4080"]


def word(n: int) -> str:
    return WORDS[n] if n < len(WORDS) else f"{n:,}"


def quarter(day: str) -> int:
    return (int(day[5:7]) + 2) // 3


def runs(numbers: list[str]) -> list[str]:
    """Document numbers grouped by year as the notes list them: three or more consecutive numbers as "first to
    last", two as "first and last", the later numbers shortened to their sequence."""
    by_prefix = defaultdict(list)
    for n in sorted(numbers):
        prefix, seq = n.rsplit("-", 1)
        by_prefix[prefix].append(seq)
    out = []
    for prefix, seqs in by_prefix.items():
        ints = [int(s) for s in seqs]
        consecutive = ints == list(range(ints[0], ints[0] + len(ints)))
        if len(seqs) >= 3 and consecutive:
            out.append(f"{prefix}-{seqs[0]} to {seqs[-1]}")
        elif len(seqs) == 2:
            out.append(f"{prefix}-{seqs[0]} and {seqs[1]}")
        else:
            out.append(", ".join(f"{prefix}-{s}" for s in seqs))
    return out


def dates(days: list[str]) -> str:
    """Dates as the notes list them: two as "first and last", more as "first to last", the second without its year
    when it is in the same year."""
    days = sorted(set(days))
    second = days[-1][5:] if days[-1][:4] == days[0][:4] else days[-1]
    if len(days) == 1:
        return days[0]
    return f"{days[0]} and {second}" if len(days) == 2 else f"{days[0]} to {second}"


# --- the sales star --------------------------------------------------------------------------------

def lines(d) -> list[dict]:
    """The fact table of the sales star, one row per invoice line, with its shipment date (Exercise 14.2)."""
    if getattr(d, "_ch14_lines", None) is None:
        rows = d.q("SELECT l.SalesInvoiceLineID, l.SalesInvoiceID, si.InvoiceNumber, si.InvoiceDate, si.CustomerID, "
                   "i.ItemGroup, l.Quantity, l.UnitPrice, l.Discount, l.LineTotal, l.Quantity * l.BaseListPrice, "
                   "l.Quantity * l.UnitPrice * l.Discount, l.Quantity * i.StandardCost, sh.ShipmentDate "
                   "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "JOIN Item i ON i.ItemID = l.ItemID LEFT JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID "
                   "LEFT JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID ORDER BY l.SalesInvoiceLineID")
        d._ch14_lines = [dict(id=r[0], invoice=r[1], number=r[2], date=r[3], customer=r[4], group=r[5], qty=r[6],
                              price=r[7], discount=r[8], rev=r[9], list=r[10], disc=r[11], cost=r[12], shipped=r[13],
                              year=int(r[3][:4]), month=int(r[3][5:7]), quarter=quarter(r[3])) for r in rows]
    return d._ch14_lines


def pick(d, **match) -> list[dict]:
    return [r for r in lines(d) if all(r[k] == v for k, v in match.items())]


def total(rows: list[dict], field: str) -> float:
    return sum(r[field] for r in rows)


def groups(d) -> list[str]:
    return sorted({r["group"] for r in lines(d)})


def design_services(d) -> bool:
    """Every Services item on the invoice lines is a design service (item codes DSV-)."""
    return d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID "
                 "WHERE i.ItemGroup = 'Services' AND i.ItemCode NOT LIKE 'DSV-%'") == 0


# --- the ledger star -------------------------------------------------------------------------------

def is_close(d) -> str:
    """SQL for a posting of a year-end closing entry (IsYearEndClose)."""
    return "g.VoucherNumber IN (" + ",".join(f"'{e}'" for e in d.closes) + ")"


def by_type(d, asof: str, closes: str = "asof") -> dict[str, float]:
    """Debits less credits by AccountType up to `asof`: with the closes left out only when posted on the as-of date
    (Exercise 14.1's Balance), all of them ("none", GL Amount), or none ("all")."""
    where = {"asof": f"AND NOT ({is_close(d)} AND g.PostingDate = '{asof}')", "none": f"AND NOT {is_close(d)}",
             "all": ""}[closes]
    return dict(d.q("SELECT a.AccountType, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a "
                    f"ON a.AccountID = g.AccountID WHERE g.PostingDate <= ? {where} GROUP BY 1", asof))


def net_income(d, year: int, closes: bool = False) -> float:
    """Net Income: credits less debits on the revenue and expense accounts of a fiscal year."""
    where = "" if closes else f"AND NOT {is_close(d)}"
    return d.one("SELECT SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                 f"WHERE a.AccountType IN ('Revenue', 'Expense') AND substr(g.PostingDate, 1, 4) = ? {where}", str(year))


def operating_expense(d) -> dict[str, float]:
    """Operating Expense by YearMonth (GL Amount on the Operating Expense subtype)."""
    return dict(d.q("SELECT substr(g.PostingDate, 1, 7), SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g "
                    "JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountSubType = 'Operating Expense' "
                    f"AND NOT {is_close(d)} GROUP BY 1 ORDER BY 1"))


def retained_close(d, year: int) -> str:
    """The year's second closing entry, Income Summary to Retained Earnings."""
    return d.one("SELECT EntryNumber FROM JournalEntry WHERE EntryType = 'Year-End Close - Income Summary to Retained Earnings' "
                 "AND PostingDate = ?", f"{year}-12-31")


def three_pay_months(d) -> list[str]:
    return [r[0] for r in d.q("SELECT substr(PayDate, 1, 7) FROM PayrollPeriod WHERE PayDate BETWEEN ? AND ? "
                              "GROUP BY 1 HAVING COUNT(DISTINCT PayDate) = 3 ORDER BY 1",
                              f"{d.F}-01-01", f"{d.C}-12-31")]


# --- Tutorial 14.1 ---------------------------------------------------------------------------------

@note("ch14.t1", T1)
def t1(d, claim):
    first, last = date(d.F, 1, 1), date(d.N, 12, 31)
    n_lines = d.one("SELECT COUNT(*) FROM SalesInvoiceLine")
    claim(len(lines(d)) == n_lines, "every invoice line finds its invoice (and its item) in the merge")
    lo, hi = d.one("SELECT MIN(InvoiceDate) FROM SalesInvoice"), d.one("SELECT MAX(InvoiceDate) FROM SalesInvoice")
    claim(first.isoformat() <= lo and hi <= last.isoformat(), "the Date table covers every invoice date")
    years = []
    for y in d.years:
        rows = pick(d, year=y)
        years.append(dict(year=y, lines=len(rows), revenue=total(rows, "rev"), list=total(rows, "list"),
                          discounts=total(rows, "disc"), invoices=len({r["invoice"] for r in rows})))
    # Lines dated outside the window: a year row of their own inside the Date table, (Blank) before or after it.
    outside = []
    for y in sorted({r["year"] for r in lines(d)} - set(d.years)):
        rows = pick(d, year=y)
        outside.append(dict(label=str(y) if first.year <= y <= last.year else "(Blank)", lines=len(rows),
                            revenue=total(rows, "rev"), list=total(rows, "list"), discounts=total(rows, "disc"),
                            invoices=len({r["invoice"] for r in rows}), dates=dates([r["date"] for r in rows])))
    claim(sum(y["lines"] for y in years) + sum(o["lines"] for o in outside) == n_lines, "every invoice line has a year row")
    return dict(days=(last - first).days + 1, first=first.isoformat(), last=last.isoformat(), n_lines=n_lines,
                years=years, outside=outside)


# --- Tutorial 14.2 ---------------------------------------------------------------------------------

def margin(rows: list[dict]) -> dict:
    rev, cost = total(rows, "rev"), total(rows, "cost")
    return dict(rev=rev, cost=cost, gm=rev - cost, pct=(rev - cost) / rev)


@note("ch14.t2", T2)
def t2(d, claim):
    now = pick(d, year=d.C)
    m = margin(now)
    shares = sorted(((g, total(pick(d, year=d.C, group=g), "rev") / m["rev"]) for g in groups(d)), key=lambda s: -s[1])
    furniture = total(pick(d, year=d.C, group="Furniture"), "rev")
    rate = total(now, "disc") / sum(r["qty"] * r["price"] for r in now)
    average = sum(r["discount"] for r in now) / len(now)
    quarters = []
    for y in (d.P, d.C):
        for qn in range(1, 5):
            qm = margin(pick(d, year=y, group="Furniture", quarter=qn))
            quarters.append(dict(label=f"{y}-Q{qn}" if qn == 1 else f"Q{qn}", **qm))
    rates = []
    for qn in range(1, 5):
        rows = pick(d, year=d.C, group="Furniture", quarter=qn)
        rates.append(total(rows, "disc") / sum(r["qty"] * r["price"] for r in rows))
    return dict(rev=m["rev"], n=len(now), invoices=len({r["invoice"] for r in now}), cost=m["cost"], gm=m["gm"],
                pct={y: margin(pick(d, year=y))["pct"] for y in d.years}, rate=rate, average=average,
                shares=shares, all_share=furniture / total(lines(d), "rev"), furniture=furniture, quarters=quarters,
                q3=quarters[-2]["gm"], q4=quarters[-1]["gm"], rates=rates)


# --- Tutorial 14.3 ---------------------------------------------------------------------------------

@note("ch14.t3", T3)
def t3(d, claim):
    n_gl = d.one("SELECT COUNT(*) FROM GLEntry")
    closes = []
    previous = None
    for e in d.closes:
        prefix = e.rsplit("-", 1)[0]
        closes.append(dict(number=e if prefix != previous else "-" + e.rsplit("-", 1)[1],
                           postings=d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber = ?", e)))
        previous = prefix
    claim(len(d.closes) == 2 * len(d.years) and all(len(d.closes_of(y)) == 2 for y in d.years),
          "two closing entries for each fiscal year")
    matched, journal = d.q("SELECT COUNT(*), SUM(g.SourceDocumentType = 'JournalEntry') FROM GLEntry g "
                           "WHERE g.VoucherNumber IN (SELECT EntryNumber FROM JournalEntry)")[0]
    je_rows = d.one("SELECT COUNT(*) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    claim(matched == journal == je_rows, "VoucherNumber equals an EntryNumber only on the JournalEntry postings, and on all of them")
    ni = [net_income(d, y) for y in d.years]
    for y, v in zip(d.years, ni):
        moved = d.one("SELECT g.Credit FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                      "WHERE g.VoucherNumber = ? AND a.AccountName = 'Retained Earnings'", retained_close(d, y))
        claim(abs(moved - v) < 0.005, f"the net income of {y} equals its Income Summary to Retained Earnings close")
        claim(abs(net_income(d, y, closes=True)) < 0.005, f"with the closes included, net income of {y} is zero")
    sub = dict(d.q("SELECT a.AccountSubType, SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g JOIN Account a "
                   "ON a.AccountID = g.AccountID WHERE a.AccountType IN ('Revenue', 'Expense') "
                   f"AND substr(g.PostingDate, 1, 4) = ? AND NOT {is_close(d)} GROUP BY 1", str(d.C)))
    named = ["Operating Revenue", "Contra Revenue", "COGS", "Operating Expense", "Other Expense", "Other Income or Expense"]
    claim(set(sub) == set(named), "the six subtypes listed are all the income statement subtypes")
    opex = operating_expense(d)
    months = [f"{y}-{m:02d}" for y in d.years for m in range(1, 13)]
    claim(set(opex) <= set(months), "operating expense is posted only in the fiscal years of the window")
    values = [opex.get(m) for m in months]
    deviation = {}
    for i, m in enumerate(months):
        window = values[max(0, i - 3):i]
        if window and values[i] is not None:
            expected = sum(v or 0 for v in window) / len(window)
            deviation[m] = (values[i] - expected) / expected
    spikes = [m for m in months if m in deviation and deviation[m] > 0.2]
    paydays = three_pay_months(d)
    claim(months[0] not in deviation, f"{months[0]} has no expectation (blank)")
    claim(spikes[0] == f"{d.F}-02", "the first month above 20% is the second month of the data")
    invoices = [n for _, n in d.q("SELECT substr(InvoiceDate, 1, 7), COUNT(*) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) "
                                  "BETWEEN ? AND ? GROUP BY 1 ORDER BY 1", str(d.F), str(d.C))]
    claim(invoices[0] < 0.75 * sorted(invoices)[len(invoices) // 2], f"January {d.F} is a start-up month (few invoices)")
    claim(spikes[1:] == paydays, "the other months above 20% are exactly the months with three pay dates")
    rest = [v for m, v in deviation.items() if m not in spikes]
    by_year = [sum(v for m, v in opex.items() if m.startswith(str(y))) for y in d.years]
    accounts, debit, credit = trial_balance(d, f"{d.C}-12-31")
    claim(abs(debit - credit) < 0.005, "the debit and credit balances are equal")
    return dict(n_gl=n_gl, closes=closes, journal=je_rows, ni=list(zip(d.years, ni)), sub=sub, by_year=by_year,
                first_spike=dict(month=spikes[0], dev=deviation[spikes[0]]),
                paydays=[dict(month=m, dev=deviation[m]) for m in paydays], n_paydays=word(len(paydays)),
                low=min(rest), high=max(rest), blank=months[0], accounts=accounts, tb=debit)


def trial_balance(d, asof: str) -> tuple[int, float, float]:
    """Test 3: the accounts with postings up to the as-of date without that date's two closes, and the totals of
    their debit and credit balances."""
    balances = [b for (b,) in d.q("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE PostingDate <= ? AND "
                                  "VoucherNumber NOT IN (?, ?) GROUP BY AccountID", asof, *d.closes_of(int(asof[:4])))]
    return len(balances), sum(b for b in balances if b > 0), -sum(b for b in balances if b < 0)


# --- Exercise 14.1 ---------------------------------------------------------------------------------

TYPES = ["Asset", "Liability", "Equity", "Revenue", "Expense"]


def month_end(year: int, month: int) -> str:
    following = date(year + month // 12, month % 12 + 1, 1)
    return date.fromordinal(following.toordinal() - 1).isoformat()


def zero(x: float) -> float:
    """A total that rounds to zero, without a minus sign."""
    return 0.0 if abs(x) < 0.005 else x


@note("ch14.ex1", EXERCISES)
def ex1(d, claim):
    asof = f"{d.C}-12-31"
    now, mid, first = (by_type(d, a) for a in (asof, month_end(d.C, 6), f"{d.F}-12-31"))
    for label, b in (("December", now), ("June", mid), ("the first year-end", first)):
        claim(set(b) <= set(TYPES), "the five account types are all the types with balances")
        claim(abs(sum(b.values())) < 0.005, f"the balance at {label} totals zero")
    ni = net_income(d, d.C)
    claim(abs(now["Revenue"] + now["Expense"] + ni) < 0.005,
          f"revenue and expense together at {d.C}-12 equal the net income of fiscal {d.C}")
    claim(abs(-now["Liability"] - now["Equity"] + ni - now["Asset"]) < 0.005,
          "assets equal liabilities, equity, and net income")
    claim(len(d.years) == 3, "the window holds three fiscal years, so the closes before the current year are those of the first and prior years")
    claim(all(d.closes_of(y) for y in d.years[:-1]), "the closes of the earlier years are dated December 31 of those years")
    claim(abs(first["Revenue"] + first["Expense"] + net_income(d, d.F)) < 0.005,
          "revenue and expense at the first year-end equal that year's net income")
    kept, none = by_type(d, asof, "all"), by_type(d, asof, "none")
    claim(abs(kept["Revenue"]) < 0.005 and abs(kept["Expense"]) < 0.005,
          "with every close kept, the revenue and expense accounts are zero at the year-end")
    opening = d.one("SELECT SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                    "JOIN JournalEntry j ON j.EntryNumber = g.VoucherNumber WHERE a.AccountType = 'Equity' "
                    "AND j.EntryType = 'Opening'")
    claim(abs(none["Equity"] - opening) < 0.005, "on GL Amount, equity is the opening equity only")
    claim(abs(none["Equity"] - first["Equity"]) < 0.005, "the opening equity equals the equity at the first year-end")
    claim(abs(kept["Asset"] - now["Asset"]) < 0.005 and abs(none["Asset"] - now["Asset"]) < 0.005,
          "assets are the same in all three measures")
    contra = d.q("SELECT AccountNumber, AccountName, AccountType, NormalBalance FROM Account WHERE "
                 "(AccountType IN ('Asset', 'Expense') AND NormalBalance = 'Credit') OR "
                 "(AccountType IN ('Liability', 'Equity', 'Revenue') AND NormalBalance = 'Debit') ORDER BY AccountNumber")
    assets = [r for r in contra if r[2] == "Asset"]
    depreciation = [r[0] for r in assets if "Accumulated Depreciation" in r[1]]
    allowance = [r for r in assets if "Accumulated Depreciation" not in r[1]]
    equity = [r for r in contra if r[2] == "Equity"]
    revenue = [r for r in contra if r[2] == "Revenue"]
    claim(len(allowance) == 1 and allowance[0] == assets[0] and len(equity) == 1 and len(revenue) == 2
          and len(assets) + len(equity) + len(revenue) == len(contra),
          "the contra accounts are one allowance and the accumulated depreciation accounts (assets), one equity account, "
          "and two revenue accounts, and no liability or expense account")
    contra_9 = d.one("SELECT COUNT(*) FROM Account WHERE AccountName LIKE '%Allowance%' OR AccountName LIKE "
                     "'%Accumulated Depreciation%' OR AccountName LIKE '%Dividends%' OR AccountName LIKE 'Sales Returns%' "
                     "OR AccountName LIKE 'Sales Discounts%'")
    claim(contra_9 == len(contra), "the accounts are the contra accounts of Chapter 9")
    return dict(asof=asof, now={k: now[k] for k in TYPES}, total=zero(sum(now.values())), ni=ni, liab=-now["Liability"],
                equity=-now["Equity"], mid={k: mid[k] for k in TYPES}, first={k: first[k] for k in TYPES},
                ni_first=net_income(d, d.F), kept_equity=kept["Equity"], gl=none, years=word(len(d.years)),
                n_contra=word(len(contra)).capitalize(), allowance=dict(number=allowance[0][0], name=allowance[0][1]),
                depreciation=depreciation, equity_contra=dict(number=equity[0][0], name=equity[0][1]),
                revenue=[dict(number=r[0], name=r[1]) for r in revenue])


# --- Exercise 14.2 ---------------------------------------------------------------------------------

def posted_late(d, year: int) -> list[dict]:
    """Chapter 12's revenue cutoff test (test L5): the invoices for deliveries of `year` whose revenue was posted in
    another year, with their SubTotal."""
    rows = d.q("WITH Shipped AS (SELECT sil.SalesInvoiceID, MAX(s.DeliveryDate) AS DeliveryDate FROM SalesInvoiceLine sil "
               "JOIN ShipmentLine sl ON sl.ShipmentLineID = sil.ShipmentLineID JOIN Shipment s ON s.ShipmentID = sl.ShipmentID "
               "GROUP BY sil.SalesInvoiceID), Posted AS (SELECT SourceDocumentID AS SalesInvoiceID, MIN(PostingDate) AS "
               "PostingDate FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' GROUP BY SourceDocumentID) "
               "SELECT si.InvoiceNumber, si.InvoiceDate, p.PostingDate, si.SubTotal FROM SalesInvoice si "
               "JOIN Shipped sh ON sh.SalesInvoiceID = si.SalesInvoiceID JOIN Posted p ON p.SalesInvoiceID = si.SalesInvoiceID "
               "WHERE substr(sh.DeliveryDate, 1, 4) = ? AND substr(p.PostingDate, 1, 4) <> substr(sh.DeliveryDate, 1, 4) "
               "ORDER BY si.InvoiceNumber", str(year))
    return [dict(number=r[0], date=r[1], posted=r[2], sub=r[3]) for r in rows]


@note("ch14.ex2", EXERCISES)
def ex2(d, claim):
    rows = lines(d)
    shipped = [r for r in rows if r["shipped"]]
    blank = [r for r in rows if not r["shipped"]]
    services = [r for r in rows if r["group"] == "Services"]
    claim({r["id"] for r in blank} == {r["id"] for r in services}, "the lines without a shipment are exactly the Services lines")
    claim({int(r["shipped"][:4]) for r in shipped} == set(d.years), "the ship dates fall in the fiscal years of the window")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE substr(DeliveryDate, 1, 4) <> substr(ShipmentDate, 1, 4)") == 0,
          "every shipment is delivered in the year it ships")
    by_invoice = [total(pick(d, year=y), "rev") for y in d.years]
    before = [r for r in rows if r["year"] < d.F]       # dated before the Date table: (Blank) on the active relationship
    by_ship = [sum(r["rev"] for r in shipped if int(r["shipped"][:4]) == y) for y in d.years]
    by_services = [total(pick(d, year=y, group="Services"), "rev") for y in d.years]
    for y, inv, shp, srv in zip(d.years, by_invoice, by_ship, by_services):
        claim(shp < inv and srv > abs(inv - shp - srv),
              f"revenue by ship date is lower in {y} mainly because Services drop to (Blank)")
    cross = [r for r in shipped if r["shipped"][:4] != r["date"][:4]]
    late, early = [], []
    for y in d.years:
        group = [r for r in cross if r["year"] == y and r["shipped"][:4] < r["date"][:4]]
        if group:
            claim(all(r["shipped"][:7] == f"{y - 1}-12" and r["date"][:7] == f"{y}-01" for r in group),
                  f"the invoices dated in {y} for earlier shipments are dated in January for shipments of December {y - 1}")
            posted = {p for (p,) in d.q("SELECT DISTINCT substr(PostingDate, 1, 7) FROM GLEntry WHERE SourceDocumentType = "
                                        "'SalesInvoice' AND SourceDocumentID IN (%s)" % ",".join(str(r["invoice"]) for r in group))}
            claim(posted == {f"{y}-01"}, f"the invoices for December {y - 1} shipments were posted in January {y}")
            late.append(dict(lines=len(group), invoices=len({r["invoice"] for r in group}), first=min(r["date"] for r in group),
                             last=max(r["date"] for r in group), ship_year=y - 1, amount=total(group, "rev")))
        group = [r for r in cross if int(r["shipped"][:4]) == y and r["shipped"][:4] > r["date"][:4]]
        if group:
            claim(len({r["shipped"] for r in group}) == 1, f"the invoices dated before their {y} shipment all shipped on one date")
            claim(all(int(r["number"][3:7]) == r["year"] + 1 for r in group),
                  "the invoices dated before their shipment carry the next year's prefix")
            early.append(dict(lines=len(group), invoices=len({r["invoice"] for r in group}),
                              numbers=runs(sorted({r["number"] for r in group}))[0],
                              dates=dates([r["date"] for r in group]), shipped=group[0]["shipped"], amount=total(group, "rev")))
    claim([g["ship_year"] for g in late] == [d.F, d.P], "the late invoices are for shipments of the first and prior years")
    # Chapter 12's test dates an invoice by its last delivery and its first posting, so against this exercise's late
    # invoices of the current year it adds the invoices dated in the prior year and posted in the current one, and
    # leaves out an invoice whose lines were also delivered in the current year.
    ch12 = posted_late(d, d.P)
    numbers = {r["number"] for r in cross if r["year"] == d.C and r["shipped"][:4] < r["date"][:4]}
    added = [i for i in ch12 if i["number"] not in numbers]
    claim(all(i["date"][:4] == str(d.P) and i["posted"][:4] == str(d.C) for i in added),
          f"the invoices Chapter 12 adds are dated in {d.P} and posted in {d.C}")
    dropped = sorted(numbers - {i["number"] for i in ch12})
    last = dict(d.q("WITH s AS (SELECT si.InvoiceNumber, MAX(sh.DeliveryDate) AS last FROM SalesInvoice si "
                    "JOIN SalesInvoiceLine l ON l.SalesInvoiceID = si.SalesInvoiceID JOIN ShipmentLine sl "
                    "ON sl.ShipmentLineID = l.ShipmentLineID JOIN Shipment sh ON sh.ShipmentID = sl.ShipmentID "
                    "GROUP BY 1) SELECT InvoiceNumber, last FROM s"))
    claim(all(last[n][:4] == str(d.C) for n in dropped),
          f"the invoices Chapter 12 leaves out also have lines delivered in {d.C}")
    kept = numbers - set(dropped)
    claim(abs(sum(i["sub"] for i in ch12) - sum(r["rev"] for r in cross if r["number"] in kept)
              - sum(i["sub"] for i in added)) < 0.005,
          "Chapter 12's SubTotal is the crossing lines' amount of the invoices it keeps plus the added invoices'")
    return dict(by_invoice=by_invoice, by_ship=by_ship, blank=total(blank, "rev"), n_services=len(services),
                by_services=by_services, all=total(rows, "rev"), n_shipped=len(shipped), n_cross=len(cross), late=late,
                before=dict(n=len(before), rev=total(before, "rev")), ch12=dict(n=len(ch12), sub=sum(i["sub"] for i in ch12)),
                added=[dict(number=i["number"], posted=i["posted"]) for i in added], dropped=runs(dropped) if dropped else [],
                early=early)


# --- Exercise 14.3 ---------------------------------------------------------------------------------

def monthly(d, group: str, year: int) -> list[float]:
    return [total(pick(d, group=group, year=year, month=m), "rev") for m in range(1, 13)]


def swing(d, group: str) -> dict:
    """A group's monthly changes against the prior year in the current fiscal year, and their spread."""
    now, before = monthly(d, group, d.C), monthly(d, group, d.P)
    yoy = [a / b - 1 for a, b in zip(now, before)]
    low, high = min(range(12), key=lambda i: yoy[i]), max(range(12), key=lambda i: yoy[i])
    return dict(yoy=yoy, low=yoy[low], low_month=MONTHS[low], high=yoy[high], high_month=MONTHS[high],
                spread=yoy[high] - yoy[low])


@note("ch14.ex3", EXERCISES)
def ex3(d, claim):
    now, before = monthly(d, "Furniture", d.C), monthly(d, "Furniture", d.P)
    yoy = [a / b - 1 for a, b in zip(now, before)]
    low, high = min(range(12), key=lambda i: yoy[i]), max(range(12), key=lambda i: yoy[i])
    ledger = {(int(y), int(m)): v for y, m, v in d.q(
        "SELECT substr(PostingDate, 1, 4), substr(PostingDate, 6, 2), SUM(Credit) - SUM(Debit) FROM GLEntry "
        "WHERE AccountID = ? AND SourceDocumentType <> 'JournalEntry' GROUP BY 1, 2", d.account("4010"))}
    gap = [ledger.get((d.C, m + 1), 0.0) - now[m] for m in range(12)]
    claim(all(abs(g) < 0.005 for g in gap[1:]), f"the ledger's Furniture revenue of {d.C} differs from the lines only in January")
    crossing = d.q("SELECT si.InvoiceNumber, SUM(g.Credit) - SUM(g.Debit), MIN(si.InvoiceDate) FROM GLEntry g JOIN SalesInvoice si "
                   "ON si.SalesInvoiceID = g.SourceDocumentID WHERE g.SourceDocumentType = 'SalesInvoice' AND g.AccountID = ? "
                   "AND substr(si.InvoiceDate, 1, 4) = ? AND substr(g.PostingDate, 1, 4) = ? GROUP BY 1",
                   d.account("4010"), str(d.P), str(d.C))
    claim(len(crossing) == 1 and abs(crossing[0][1] - gap[0]) < 0.005,
          f"the January difference is the one Furniture invoice dated in {d.P} and posted in {d.C}")
    crossed = int(crossing[0][2][5:7]) - 1 if crossing else None        # the prior-year month the ledger moves it from
    extremes = []
    for i in sorted({low, high}):
        before_ledger = ledger.get((d.P, i + 1), 0.0)
        on_ledger = ledger.get((d.C, i + 1), 0.0) / before_ledger - 1 if before_ledger else 0.0
        same = abs(on_ledger - yoy[i]) < 0.0005
        claim(same or i == crossed, f"{MONTHS[i]}'s change differs from the ledger's only through the invoice that crosses")
        extremes.append(dict(name=MONTHS[i], same=same, ledger=on_ledger))
    ytd = [sum(now[:m + 1]) / sum(before[:m + 1]) - 1 for m in range(12)]
    by_group = [dict(group=g, now=total(pick(d, group=g, year=d.C), "rev"), before=total(pick(d, group=g, year=d.P), "rev"))
                for g in groups(d)]
    swings = sorted(groups(d), key=lambda g: -swing(d, g)["spread"])
    claim(swings[:2] == ["Services", "Textiles"], "Services swings the most, and Textiles next")
    services = [r for r in pick(d, group="Services", year=d.C)]
    per_month = [[r for r in services if r["month"] == m] for m in range(1, 13)]
    largest = max(services, key=lambda r: r["rev"])
    claim(design_services(d), "the Services lines are design services")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ?", str(d.N)) == 0,
          f"no invoice is dated in {d.N}, so the {d.N} row has no revenue")
    return dict(months=[dict(name=MONTHS[m], yoy=yoy[m], now=now[m], before=before[m], detail=m >= 9 or m in (low, high))
                        for m in range(12)],
                low=MONTHS[low], high=MONTHS[high], extremes=extremes,
                crossing=crossing[0][0] if crossing else "", crossed=MONTHS[crossed] if crossing else "",
                ytd=ytd, ytd_sign="positive" if all(v > 0 for v in ytd[:9]) else "negative" if all(v < 0 for v in ytd[:9]) else "",
                by_group=by_group,
                now_total=sum(g["now"] for g in by_group), before_total=sum(g["before"] for g in by_group),
                services=swing(d, "Services"), textiles=swing(d, "Textiles"),
                lines_low=min(len(p) for p in per_month), lines_high=max(len(p) for p in per_month),
                cust_low=min(len({r["customer"] for r in p}) for p in per_month),
                cust_high=max(len({r["customer"] for r in p}) for p in per_month),
                customers=len({r["customer"] for r in services}), largest=largest["rev"],
                largest_month=MONTHS[largest["month"] - 1])


# --- Exercise 14.4 ---------------------------------------------------------------------------------

def quarter_totals(rows: list[dict]) -> dict:
    units = total(rows, "qty")
    rev, cost, lst, disc = (total(rows, f) for f in ("rev", "cost", "list", "disc"))
    return dict(units=units, gm=rev - cost, list_margin=(lst - cost) / units, reduction=(lst - rev - disc) / units,
                discount=disc / units)


def bridge(d, group: str, year: int, qn: int) -> dict:
    """Exercise 14.4's measures for one quarter: Margin PQ, the four effects, Gross Margin, and Bridge Check."""
    py, pq = (year, qn - 1) if qn > 1 else (year - 1, 4)
    a = quarter_totals(pick(d, group=group, year=py, quarter=pq))
    b = quarter_totals(pick(d, group=group, year=year, quarter=qn))
    out = dict(pq=a["gm"], volume=(b["units"] - a["units"]) * a["gm"] / a["units"],
               mix=b["units"] * (b["list_margin"] - a["list_margin"]),
               lists=-b["units"] * (b["reduction"] - a["reduction"]),
               promotions=-b["units"] * (b["discount"] - a["discount"]), gm=b["gm"], units=b["units"], pq_units=a["units"])
    out["check"] = out["pq"] + out["volume"] + out["mix"] + out["lists"] + out["promotions"] - out["gm"]
    return out


@note("ch14.ex4", EXERCISES)
def ex4(d, claim):
    quarters = [dict(label=f"Q{qn}", **bridge(d, "Furniture", d.C, qn)) for qn in range(1, 5)]
    claim(all(abs(q["check"]) < 0.005 for q in quarters), "Bridge Check is zero in every row")
    q3, q4 = quarters[2], quarters[3]
    promotion = d.q("SELECT PromotionID, EffectiveStartDate FROM PromotionProgram WHERE ScopeType = 'ItemGroup' "
                    "AND ItemGroup = 'Furniture' AND substr(EffectiveStartDate, 1, 4) = ?", str(d.C))
    claim(len(promotion) == 1, f"one promotion covers the Furniture item group in {d.C}")
    pid, start = promotion[0] if promotion else (None, f"{d.C}-09-01")
    first = d.one("SELECT MIN(si.InvoiceDate) FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = "
                  "l.SalesInvoiceID WHERE l.PromotionID = ?", pid)
    claim(first is not None and first[:7] == start[:7] and quarter(start) == 3,
          "the promotion's first invoiced month is its start month, in the third quarter")
    claim(q3["units"] < q3["pq_units"] and q3["volume"] < 0 and q3["promotions"] < 0,
          "the third quarter has fewer units than the second (volume) and a negative promotion effect")
    decline = q4["pq"] - q4["gm"]
    # Chapter 6's storyline (Part II): the fourth quarter's decline is a promotion (price) effect.
    claim(-q4["promotions"] > decline > 0 and all(abs(q4[k]) < 0.1 * abs(q4["promotions"]) for k in ("volume", "mix", "lists")),
          "in the fourth quarter, the promotion effect is larger than the whole decline, and volume, mix and price lists "
          "are small beside it (Chapter 6's storyline)")
    lighting = bridge(d, "Lighting", d.C, 4)
    claim(abs(lighting["check"]) < 0.005, "the Lighting bridge checks")
    names = dict(volume="volume", mix="mix", lists="price-list", promotions="promotion")
    main = max(names, key=lambda k: abs(lighting[k]))
    return dict(quarters=quarters, promotion=pid, start_month=MONTHS[int(start[5:7]) - 1], lighting=lighting,
                main=dict(name=names[main], direction="decline" if lighting[main] < 0 else "increase",
                          price=main in ("lists", "promotions")))


# --- Exercise 14.5 ---------------------------------------------------------------------------------

def opex_on(d, days: set[str] | None) -> float:
    """Operating Expense of the current fiscal year, on the given posting dates (all of them if None)."""
    rows = d.q("SELECT g.PostingDate, SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
               f"WHERE a.AccountSubType = 'Operating Expense' AND NOT {is_close(d)} AND substr(g.PostingDate, 1, 4) = ? "
               "GROUP BY 1", str(d.C))
    return sum(v for day, v in rows if days is None or day in days)


@note("ch14.ex5", EXERCISES)
def ex5(d, claim):
    customers = d.one("SELECT COUNT(*) FROM Customer")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice si LEFT JOIN Customer c ON c.CustomerID = si.CustomerID "
                "WHERE c.CustomerID IS NULL") == 0,
          "every invoice's customer is in the Customer table, so Customer Rows Both equals Customers Invoiced")
    now = pick(d, year=d.C)
    invoiced = [dict(group=g, n=len({r["customer"] for r in now if r["group"] == g})) for g in groups(d)]
    opex = opex_on(d, None)
    year_days = (date(d.C, 12, 31) - date(d.C, 1, 1)).days + 1
    leak = []
    for g in groups(d):
        days = {r["date"] for r in now if r["group"] == g}
        leak.append(dict(group=g, opex=opex_on(d, days), days=len(days)))
    others = [x for x in leak if x["group"] != "Services"]
    services = next(x for x in leak if x["group"] == "Services")
    claim(services["days"] == min(x["days"] for x in leak), "Services has the fewest invoice days")
    claim(design_services(d), "the Services lines are design services")
    rev = total(now, "rev")
    every = total(lines(d), "rev")
    shares = [dict(group=g, rf=total([r for r in now if r["group"] == g], "rev") / rev,
                   all=total([r for r in now if r["group"] == g], "rev") / every) for g in groups(d)]
    outside = [r for r in lines(d) if r["year"] not in d.years]
    claim({r["year"] for r in lines(d)} >= set(d.years) and total(outside, "rev") < 0.001 * every,
          "the invoice lines span the fiscal years of the window, but for a few dated outside it")
    return dict(customers=customers, invoiced=invoiced, n_invoiced=len({r["customer"] for r in now}), opex=opex,
                others=others, services=services, services_word=word(services["days"]), year_days=year_days,
                shares=shares, all_total=rev / every, every=every, years=word(len(d.years)),
                outside=dict(n=len(outside), dates=dates([r["date"] for r in outside])) if outside else None)


# --- Exercise 14.6 ---------------------------------------------------------------------------------

@note("ch14.ex6", EXERCISES)
def ex6(d, claim):
    now = pick(d, year=d.C)
    ni = net_income(d, d.C)
    close = retained_close(d, d.C)
    moved = d.one("SELECT SUM(Credit) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
                  "WHERE g.VoucherNumber = ? AND a.AccountName = 'Retained Earnings'", close)
    claim(abs(moved - ni) < 0.005, f"the net income of {d.C} equals {close}")
    debits = d.one("SELECT SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'JournalEntry'")
    claim(abs(debits - d.one("SELECT SUM(TotalAmount) FROM JournalEntry")) < 0.005,
          "the journal entry debits equal JournalEntry TotalAmount")
    variance = d.one(f"SELECT SUM(g.Debit) - SUM(g.Credit) FROM GLEntry g WHERE g.AccountID = ? AND NOT {is_close(d)} "
                     "AND substr(g.PostingDate, 1, 4) = ?", d.account("5080"), str(d.C))
    ids = ",".join(str(d.account(n)) for n in REVENUE)
    ledger = d.one(f"SELECT SUM(Credit) - SUM(Debit) FROM GLEntry WHERE SourceDocumentType = 'SalesInvoice' "
                   f"AND AccountID IN ({ids}) AND substr(PostingDate, 1, 4) = ?", str(d.C))
    rev = total(now, "rev")
    crossing = d.q("SELECT si.InvoiceNumber, MIN(g.PostingDate), SUM(g.Credit) - SUM(g.Debit) FROM GLEntry g "
                   "JOIN SalesInvoice si ON si.SalesInvoiceID = g.SourceDocumentID WHERE g.SourceDocumentType = 'SalesInvoice' "
                   f"AND g.AccountID IN ({ids}) AND substr(si.InvoiceDate, 1, 4) = ? AND substr(g.PostingDate, 1, 4) = ? "
                   "GROUP BY 1 ORDER BY 1", str(d.P), str(d.C))
    claim(abs(ledger - rev - sum(c[2] for c in crossing)) < 0.005,
          f"the ledger exceeds the lines by exactly the invoices dated in {d.P} and posted in {d.C}")
    claim(all(c[1] == f"{d.C}-01-01" for c in crossing), f"those invoices were posted on {d.C}-01-01")
    claim(all(d.one("SELECT InvoiceDate FROM SalesInvoice WHERE InvoiceNumber = ?", c[0]) >= f"{d.P}-10-01" for c in crossing),
          f"those invoices are dated late in {d.P} (its fourth quarter)")
    claim(ledger > rev, "the ledger exceeds the lines")
    claim(abs(net_income(d, d.C, closes=True)) < 0.005, "with the closes kept, the net income is 0")
    claim(abs(d.one("SELECT SUM(Debit) - SUM(Credit) FROM GLEntry WHERE AccountID = ? AND substr(PostingDate, 1, 4) = ?",
                    d.account("5080"), str(d.C))) < 0.005, "with the closes kept, 5080 is 0")
    return dict(n=len(now), rev=rev, ni=ni, close=close, debits=debits, variance=variance, ledger=ledger,
                gap=ledger - rev, numbers=runs([c[0] for c in crossing])[0] if crossing else "",
                amounts=[c[2] for c in crossing])


# --- Multiple-choice answer key --------------------------------------------------------------------

@note("ch14.mcq", MCQ)
def mcq(d, claim):
    now = pick(d, year=d.C)
    days = len({r["date"] for r in now if r["group"] == "Services"})
    claim(opex_on(d, {r["date"] for r in now if r["group"] == "Services"}) > 0,
          "the Services days leave some operating expense")
    furniture = total(pick(d, year=d.C, group="Furniture"), "rev")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ?", str(d.N)) == 0,
          f"no invoice is dated in {d.N}")
    return dict(days=days, all_share=furniture / total(lines(d), "rev"), rf_share=furniture / total(now, "rev"))
