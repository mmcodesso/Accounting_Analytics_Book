"""Expected values for the Solution Notes checks, computed from CharlesRiver.sqlite (read-only), independently of Excel.

Each value reproduces what the tutorial's formula returns: Excel's ROUND rounds half away from zero (xround), and
PERCENTILE.INC interpolates between ranks (percentile_inc), both from scripts/figures/excel.py.
"""

from __future__ import annotations

import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from functools import cached_property
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "figures"))
from paths import db_uri  # noqa: E402
from excel import percentile_inc, xround  # noqa: E402

GROUPS = ["Furniture", "Lighting", "Textiles", "Accessories", "Services"]
METHODS = ["Approved Override", "Base List", "Customer Price List", "Segment Price List"]
RATES = [0, 0.08, 0.1, 0.12]


def quarter(iso: str) -> str:
    return f"{iso[:4]}-Q{(int(iso[5:7]) + 2) // 3}"


class Expected:
    def __init__(self, year: int):
        self.year = year                      # the report year of the tutorials (Phase 7 turns it into a token)
        con = sqlite3.connect(db_uri(), uri=True)
        q = lambda sql: con.execute(sql).fetchall()
        self.invoices = {r[0]: dict(date=r[1], due=r[2], order=r[3], customer=r[4], subtotal=r[5])
                         for r in q("SELECT SalesInvoiceID, InvoiceDate, DueDate, SalesOrderID, CustomerID, SubTotal "
                                    "FROM SalesInvoice")}
        self.items = {r[0]: dict(code=r[1], group=r[2], cost=r[3], list=r[4])
                      for r in q("SELECT ItemID, ItemCode, ItemGroup, StandardCost, ListPrice FROM Item")}
        self.customers = {r[0]: dict(segment=r[1], region=r[2])
                          for r in q("SELECT CustomerID, CustomerSegment, Region FROM Customer")}
        self.lines = [dict(id=r[0], inv=r[1], item=r[2], qty=r[3], blp=r[4], up=r[5], disc=r[6], lt=r[7], promo=r[8],
                           method=r[9])
                      for r in q("SELECT SalesInvoiceLineID, SalesInvoiceID, ItemID, Quantity, BaseListPrice, UnitPrice, "
                                 "Discount, LineTotal, PromotionID, PricingMethod FROM SalesInvoiceLine")]
        self.orders = {r[0]: r[1] for r in q("SELECT SalesOrderID, OrderDate FROM SalesOrder")}
        self.promotions = {r[0]: dict(code=r[1], name=r[2], pct=r[3], start=r[4], end=r[5])
                           for r in q("SELECT PromotionID, PromotionCode, PromotionName, DiscountPct, "
                                      "EffectiveStartDate, EffectiveEndDate FROM PromotionProgram")}
        con.close()

    # --- Chapter 4 -------------------------------------------------------------------------------------------------
    @cached_property
    def control(self) -> dict:
        lt = sum(l["lt"] for l in self.lines)
        st = sum(i["subtotal"] for i in self.invoices.values())
        return dict(lines=len(self.lines), invoices=len(self.invoices), line_total=lt, subtotal=st,
                    discount=sum(xround(l["qty"] * l["up"] * l["disc"]) for l in self.lines),
                    list_amount=sum(xround(l["qty"] * l["blp"]) for l in self.lines),
                    items_sold=sum(1 for i in self.items.values() if i["list"] is not None))

    def threshold(self, p: float = 0.9) -> dict:
        totals = [l["lt"] for l in self.lines]
        thr = percentile_inc(totals, p)
        large = [t for t in totals if t > thr]
        return dict(threshold=thr, large=len(large), share=sum(large) / self.control["line_total"])

    @cached_property
    def grid(self) -> dict:
        return Counter((l["method"], l["disc"]) for l in self.lines)

    def promotion(self, pid: int) -> dict:
        mine = [l for l in self.lines if l["promo"] == pid]
        return dict(lines=len(mine), discount=sum(xround(l["qty"] * l["up"] * l["disc"]) for l in mine),
                    **self.promotions[pid])

    @cached_property
    def top_promotion(self) -> int:
        counts = Counter(l["promo"] for l in self.lines if l["promo"] is not None)
        return counts.most_common(1)[0][0]

    # --- Chapter 5 -------------------------------------------------------------------------------------------------
    @cached_property
    def terms(self) -> dict:
        days = [(date.fromisoformat(i["due"]) - date.fromisoformat(i["date"])).days for i in self.invoices.values()]
        groups = Counter("Up to 30 days" if d <= 30 else "31 to 60 days" if d <= 60 else "Over 60 days" for d in days)
        return dict(groups=groups, nonstandard=sum(1 for d in days if d not in (30, 45, 60, 90)),
                    periods=len({quarter(i["date"]) for i in self.invoices.values()}))

    @cached_property
    def code_failures(self) -> int:
        def ok(c: str) -> bool:
            return len(c) == 12 and c[3] == "-" and c[7] == "-"
        return sum(1 for i in self.items.values() if i["list"] is not None and not ok(i["code"]))

    def group_by_quarter(self, group: str, year: int) -> dict[str, float]:
        out = defaultdict(float)
        for l in self.lines:
            inv = self.invoices[l["inv"]]
            if self.items[l["item"]]["group"] == group and inv["date"][:4] == str(year):
                out[quarter(inv["date"])] += l["lt"]
        return {f"{year}-Q{k}": out[f"{year}-Q{k}"] for k in range(1, 5)}

    def promotion_after_end(self, pid: int) -> int:
        end = self.promotions[pid]["end"]
        return sum(1 for l in self.lines if l["promo"] == pid and self.invoices[l["inv"]]["date"] > end)

    @cached_property
    def fractional(self) -> int:
        return sum(1 for l in self.lines if not float(l["qty"]).is_integer())

    # --- Chapter 6 -------------------------------------------------------------------------------------------------
    def year_lines(self, year: int) -> list[dict]:
        return [l for l in self.lines if self.invoices[l["inv"]]["date"][:4] == str(year)]

    def profile(self, year: int) -> dict:
        lt = [l["lt"] for l in self.year_lines(year)]
        groups = {g: dict(lines=0, revenue=0.0) for g in GROUPS}
        for l in self.year_lines(year):
            g = groups[self.items[l["item"]]["group"]]
            g["lines"] += 1
            g["revenue"] += l["lt"]
        bins = [sum(1 for t in lt if lo <= t < lo + 1000) for lo in range(0, 15000, 1000)] + \
               [sum(1 for t in lt if t >= 15000)]
        return dict(count=len(lt), total=sum(lt), average=sum(lt) / len(lt), median=statistics.median(lt),
                    stdev=statistics.stdev(lt), smallest=min(lt), largest=max(lt), p90=percentile_inc(lt, 0.9),
                    groups=groups, bins=bins)

    def margins(self, year: int) -> dict:
        rev, cost = defaultdict(float), defaultdict(float)
        for l in self.year_lines(year):
            key = (self.items[l["item"]]["group"], quarter(self.invoices[l["inv"]]["date"]))
            rev[key] += l["lt"]
            cost[key] += l["qty"] * (self.items[l["item"]]["cost"] or 0)
        return {k: (rev[k] - cost[k]) / rev[k] for k in rev}

    def segment_revenue(self, segment: str, year: int) -> float:
        return sum(l["lt"] for l in self.year_lines(year)
                   if self.customers[self.invoices[l["inv"]]["customer"]]["segment"] == segment)


# --- Chapter 6, Tutorial 6.3 ----------------------------------------------------------------------------------------

def furniture_drivers(e: Expected, year: int) -> dict[str, dict]:
    """The five Furniture totals of the third and fourth quarters, from the unrounded query columns."""
    out = {f"{year}-Q{q}": dict(qty=0.0, list=0.0, lt=0.0, disc=0.0, std=0.0) for q in (3, 4)}
    for l in e.lines:
        inv = e.invoices[l["inv"]]
        p = quarter(inv["date"])
        if p in out and e.items[l["item"]]["group"] == "Furniture":
            o = out[p]
            o["qty"] += l["qty"]
            o["list"] += l["qty"] * l["blp"]
            o["lt"] += l["lt"]
            o["disc"] += l["qty"] * l["up"] * l["disc"]
            o["std"] += l["qty"] * (e.items[l["item"]]["cost"] or 0)
    return out


def bridge(e: Expected, year: int) -> dict:
    d = furniture_drivers(e, year)
    q3, q4 = d[f"{year}-Q3"], d[f"{year}-Q4"]
    m3, m4 = q3["lt"] - q3["std"], q4["lt"] - q4["std"]
    pu = lambda x: dict(margin=(x["lt"] - x["std"]) / x["qty"], list_margin=(x["list"] - x["std"]) / x["qty"],
                        reduction=(x["list"] - x["lt"] - x["disc"]) / x["qty"], disc=x["disc"] / x["qty"])
    a, b = pu(q3), pu(q4)
    volume = (q4["qty"] - q3["qty"]) * a["margin"]
    mix = q4["qty"] * (b["list_margin"] - a["list_margin"])
    price = -q4["qty"] * (b["reduction"] - a["reduction"])
    promo = -q4["qty"] * (b["disc"] - a["disc"])
    mbd = lambda x: (x["lt"] + x["disc"] - x["std"]) / (x["lt"] + x["disc"])
    return dict(q3=m3, q4=m4, volume=volume, mix=mix, price=price, promotions=promo, cost=0.0,
                check=m3 + volume + mix + price + promo - m4, mbd3=mbd(q3), mbd4=mbd(q4), drivers=d)


def discounts_by_promotion(e: Expected, year: int, group: str = "Furniture") -> dict[tuple, tuple[int, float]]:
    out: dict[tuple, list] = defaultdict(lambda: [0, 0.0])
    for l in e.lines:
        p = quarter(e.invoices[l["inv"]]["date"])
        if p.startswith(str(year)) and e.items[l["item"]]["group"] == group:
            o = out[(l["promo"], p)]
            o[0] += 1
            o[1] += l["qty"] * l["up"] * l["disc"]
    return {k: (v[0], v[1]) for k, v in out.items()}


# --- Chapter 7 ------------------------------------------------------------------------------------------------------

def _query(sql: str, *args) -> list[tuple]:
    con = sqlite3.connect(db_uri(), uri=True)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction of the incomplete beta function (Lentz's method)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return h


def t_two_tailed(t: float, df: int) -> float:
    """Excel's T.DIST.2T: the two-tailed p-value of Student's t (the regularized incomplete beta at df/(df+t^2))."""
    import math
    x = df / (df + t * t)
    a, b = df / 2, 0.5
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    return front * _betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - front * _betacf(b, a, 1 - x) / b


def monthly_series(e: Expected, first_year: int, months: int = 36) -> list[dict]:
    rows = []
    for k in range(months):
        y, m = first_year + k // 12, k % 12 + 1
        key = f"{y}-{m:02d}"
        mine = [l for l in e.lines if e.invoices[l["inv"]]["date"][:7] == key]
        rows.append(dict(month=key, index=k + 1, revenue=sum(l["lt"] for l in mine),
                         customers=len({e.invoices[l["inv"]]["customer"] for l in mine}),
                         average=sum(l["lt"] for l in mine) / len(mine)))
    return rows


def correl(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5


def regression(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx
    sse = sum((y - intercept - slope * x) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - my) ** 2 for y in ys)
    se = (sse / (n - 2) / sxx) ** 0.5
    return dict(slope=slope, intercept=intercept, r2=1 - sse / sst, p=t_two_tailed(slope / se, n - 2), n=n)


def backtest(series: list[dict]) -> dict:
    fit = series[1:33]                                   # rows 3 to 34: MonthIndex 2 to 33
    reg = regression([r["index"] for r in fit], [r["revenue"] for r in fit])
    actual = [r["revenue"] for r in series[33:36]]
    trend = [reg["intercept"] + reg["slope"] * i for i in (34, 35, 36)]
    mean = [sum(r["revenue"] for r in fit) / len(fit)] * 3
    last = [r["revenue"] for r in series[21:24]]         # rows 23 to 25: the same months a year earlier

    def errors(f):
        return sum(f) / sum(actual) - 1, sum(abs(a - b) / b for a, b in zip(f, actual)) / 3

    out = {name: dict(values=f, quarter=sum(f), error=errors(f)[0], monthly=errors(f)[1])
           for name, f in (("trend", trend), ("mean", mean), ("last", last))}
    out["actual"] = dict(values=actual, quarter=sum(actual))
    forecast = 3 * sum(r["revenue"] for r in series[1:36]) / 35
    out["forecast"] = dict(value=forecast, low=forecast * (1 - out["mean"]["monthly"]),
                           high=forecast * (1 + out["mean"]["monthly"]))
    return out


def budget_report(e: Expected, year: int) -> dict:
    """Tutorial 7.2's BudgetReport by item group, and the lines without a planned price."""
    budget = _query("SELECT ItemID, Month, BudgetCategory, Quantity, UnitAmount, BudgetAmount FROM BudgetLine "
                    "WHERE FiscalYear = ? AND BudgetCategory IN ('Revenue', 'COGS')", year)
    planned = {(item, m): unit for item, m, cat, _, unit, _ in budget if cat == "Revenue"}
    groups = ["Furniture", "Lighting", "Textiles", "Accessories"]
    rep = {g: dict(static_rev=0.0, static_cogs=0.0, flex_rev=0.0, std=0.0, actual=0.0, budget_units=0.0, units=0.0,
                   discounts=0.0) for g in groups}
    for item, _, cat, qty, _, amount in budget:
        g = e.items[item]["group"]
        if g in rep:
            rep[g]["static_rev" if cat == "Revenue" else "static_cogs"] += amount
            if cat == "Revenue":
                rep[g]["budget_units"] += qty
    missing = 0
    for l in e.year_lines(year):
        g = e.items[l["item"]]["group"]
        if g not in rep:
            continue
        price = planned.get((l["item"], int(e.invoices[l["inv"]]["date"][5:7])))
        missing += price is None
        r = rep[g]
        r["flex_rev"] += l["lt"] if price is None else l["qty"] * price
        r["std"] += l["qty"] * (e.items[l["item"]]["cost"] or 0)
        r["actual"] += l["lt"]
        r["units"] += l["qty"]
        r["discounts"] += l["qty"] * l["up"] * l["disc"]
    for r in rep.values():
        r["static_margin"] = r["static_rev"] - r["static_cogs"]
        r["flex_margin"] = r["flex_rev"] - r["std"]
        r["actual_margin"] = r["actual"] - r["std"]
        r["volume_var"] = r["flex_margin"] - r["static_margin"]
        r["flex_var"] = r["actual_margin"] - r["flex_margin"]
    return dict(groups=rep, missing=missing)


def opex(year: int, close: str) -> dict:
    """Tutorial 7.2's operating-expense comparison and its two driver tests."""
    gl = ("FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.FiscalYear = ? "
          "AND a.AccountNumber BETWEEN 6000 AND 7999 AND g.VoucherNumber <> ?")
    bl = "FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID WHERE b.FiscalYear = ?"
    budget = dict(_query(f"SELECT a.AccountNumber, SUM(b.BudgetAmount) {bl} AND b.BudgetCategory = 'Operating Expense' "
                         "GROUP BY 1", year))
    actual = dict(_query(f"SELECT a.AccountNumber, SUM(g.Debit - g.Credit) {gl} GROUP BY 1", year, close))
    salaries_budget = _query(f"SELECT SUM(b.BudgetAmount) {bl} AND a.AccountName LIKE 'Salaries%'", year)[0][0]
    salaries_actual = _query(f"SELECT SUM(g.Debit - g.Credit) {gl} AND a.AccountName LIKE 'Salaries%'", year, close)[0][0]
    burden_budget = _query(f"SELECT SUM(b.BudgetAmount) {bl} AND a.AccountNumber = 6060", year)[0][0]
    commission_budget = _query(f"SELECT SUM(b.BudgetAmount) {bl} AND a.AccountNumber = 6290", year)[0][0]
    return dict(budget=budget, actual=actual, burden_budget=burden_budget / salaries_budget,
                burden_actual=actual.get(6060, 0) / salaries_actual, commission_budget=commission_budget,
                commission_actual=actual.get(6290, 0))


def promotion_model(e: Expected, pid: int, year: int, close: str) -> dict:
    mine = [l for l in e.lines if l["promo"] == pid]
    units = sum(l["qty"] for l in mine)
    price = (sum(l["lt"] for l in mine) + sum(l["qty"] * l["up"] * l["disc"] for l in mine)) / units
    cost = sum(l["qty"] * (e.items[l["item"]]["cost"] or 0) for l in mine) / units
    commission = opex(year, close)["commission_actual"] / sum(l["lt"] for l in e.year_lines(year))
    d = e.promotions[pid]["pct"]
    without = units * (price * (1 - commission) - cost)

    def difference(disc: float, lift: float) -> float:
        return units * (1 + lift) * (price * (1 - disc) * (1 - commission) - cost) - without

    breakeven = (price * (1 - commission) - cost) / (price * (1 - d) * (1 - commission) - cost) - 1
    return dict(units=units, price=price, cost=cost, commission=commission, discount=d, without=without,
                difference=difference, breakeven=breakeven)
