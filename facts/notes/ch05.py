"""Chapter 5's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

import re
import statistics
from datetime import date

from notes import note

EXERCISES = "chapters/05-data-preparation/_exercises.qmd"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
# Book constants: the Furniture product types of Tutorial 5.1 (tbl-05-03), and the examples the chapter's prose uses
# (chapter.qmd and Tutorial 5.1 name them), which the notes repeat.
PRODUCT_TYPES = ["BKC", "BNH", "CON", "CTB", "DSK", "NGT", "SDB", "TBL"]
CHAPTER_SIDEBOARD = "FUR-SDB-0002"
PROPER_EXAMPLES = ["Watson, Mitchell and Chen", "Donaldson LLC"]


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def series(items) -> str:
    """'a', 'a and b', or 'a, b, and c'."""
    items = [str(i) for i in items]
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def days(x: float) -> str:
    """A number of days as the notes write it: whole days without decimals, otherwise one decimal."""
    return f"{int(x):,}" if float(x).is_integer() else f"{x:,.1f}"


def percentile_inc(values, p: float) -> float:
    """Excel's PERCENTILE.INC: linear interpolation between closest ranks."""
    ordered = sorted(values)
    h = (len(ordered) - 1) * p
    lo = int(h)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (h - lo) * (ordered[hi] - ordered[lo])


def proper(text: str) -> str:
    """Excel's PROPER: a letter is capitalized after any character other than a letter, lowered otherwise."""
    out, after_letter = [], False
    for ch in text:
        if ch.isalpha():
            out.append(ch.lower() if after_letter else ch.upper())
            after_letter = True
        else:
            out.append(ch)
            after_letter = False
    return "".join(out)


def anomalies(d, kind: str) -> list[int]:
    """The primary keys the generator's AnomalyLog lists for one anomaly type."""
    keys = d.anomalies(kind)
    if keys is None:
        raise FileNotFoundError(f"no AnomalyLog beside {d.path}")
    return keys


def quarter_of(date_text: str) -> int:
    return (int(date_text[5:7]) + 2) // 3


def furniture_by_quarter(d) -> dict[int, float]:
    rows = dict(d.q("SELECT (CAST(substr(si.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, ROUND(SUM(l.LineTotal), 2) "
                    "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                    "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND substr(si.InvoiceDate, 1, 4) = ? "
                    "GROUP BY 1", str(d.C)))
    return {qn: rows.get(qn, 0.0) for qn in range(1, 5)}


def related_parties(d) -> list[tuple]:
    return d.q("SELECT s.SupplierID, s.SupplierName, e.EmployeeID, e.EmployeeName, e.JobTitle FROM Supplier s "
               "JOIN Employee e ON e.Address = s.Address AND e.City = s.City ORDER BY s.SupplierID, e.EmployeeID")


@note("ch05.ex1", EXERCISES)
def ex1(d, claim):
    gross = furniture_by_quarter(d)
    rows = {qn: (n, a) for qn, n, a in d.q(
        "SELECT (CAST(substr(cm.CreditMemoDate, 6, 2) AS INTEGER) + 2) / 3, COUNT(*), ROUND(SUM(cl.LineTotal), 2) "
        "FROM CreditMemoLine cl JOIN CreditMemo cm ON cm.CreditMemoID = cl.CreditMemoID JOIN Item i ON i.ItemID = cl.ItemID "
        "WHERE i.ItemGroup = 'Furniture' AND substr(cm.CreditMemoDate, 1, 4) = ? GROUP BY 1", str(d.C))}
    credits = [dict(q=qn, lines=rows.get(qn, (0, 0.0))[0], amount=rows.get(qn, (0, 0.0))[1]) for qn in range(1, 5)]
    net = [round(gross[c["q"]] - c["amount"], 2) for c in credits]
    unmatched = d.one("SELECT COUNT(*) FROM CreditMemoLine cl LEFT JOIN CreditMemo cm ON cm.CreditMemoID = cl.CreditMemoID "
                      "LEFT JOIN Item i ON i.ItemID = cl.ItemID WHERE cm.CreditMemoID IS NULL OR i.ItemID IS NULL")
    claim(unmatched == 0, "no credit memo line fails to match its credit memo or its item")
    earlier = d.one("SELECT COUNT(*) FROM CreditMemoLine cl JOIN CreditMemo cm ON cm.CreditMemoID = cl.CreditMemoID "
                    "JOIN SalesInvoice si ON si.SalesInvoiceID = cm.OriginalSalesInvoiceID "
                    "WHERE substr(cm.CreditMemoDate, 1, 4) = ? AND substr(si.InvoiceDate, 1, 4) < ?", str(d.C), str(d.C))
    claim(all(c["amount"] < 0.02 * gross[c["q"]] for c in credits), "the credits are small relative to revenue (under 2% each quarter)")
    claim(net[3] < net[2] and abs(credits[3]["amount"] - credits[2]["amount"]) < 0.25 * abs(gross[4] - gross[3]),
          "the credits do not explain the change between Q3 and Q4 (net revenue still falls, and the credits change little)")
    return dict(gross=[gross[qn] for qn in range(1, 5)], credits=credits, credit_lines=sum(c["lines"] for c in credits),
                credit_total=sum(c["amount"] for c in credits), net=net, earlier=earlier)


@note("ch05.ex2", EXERCISES)
def ex2(d, claim):
    prefix = d.q("SELECT InvoiceNumber, InvoiceDate FROM SalesInvoice WHERE substr(InvoiceNumber, 4, 4) <> substr(InvoiceDate, 1, 4) "
                 "ORDER BY InvoiceNumber")
    claim(all(int(n[3:7]) == int(dt[:4]) + 1 for n, dt in prefix), "every mismatched invoice carries the next year's number prefix")
    before_order = d.q("SELECT si.InvoiceNumber, si.InvoiceDate, so.OrderDate FROM SalesInvoice si "
                       "JOIN SalesOrder so ON so.SalesOrderID = si.SalesOrderID WHERE si.InvoiceDate < so.OrderDate "
                       "ORDER BY si.InvoiceNumber")
    before_shipment = {r[0] for r in d.q(
        "SELECT si.InvoiceNumber FROM SalesInvoice si JOIN (SELECT SalesOrderID, MIN(ShipmentDate) AS FirstShipment "
        "FROM Shipment GROUP BY SalesOrderID) s ON s.SalesOrderID = si.SalesOrderID WHERE si.InvoiceDate < s.FirstShipment")}
    flagged = {r[0] for r in prefix} | {r[0] for r in before_order}
    claim(flagged == before_shipment, "the invoices flagged by either test are exactly the invoices dated before their first "
                                      "shipment (Tutorial 2.1)")
    claim(d.one("SELECT COUNT(*) FROM SalesOrder WHERE substr(OrderNumber, 4, 4) <> substr(OrderDate, 1, 4)") == 0 and
          d.one("SELECT COUNT(*) FROM Shipment WHERE substr(ShipmentNumber, 4, 4) <> substr(ShipmentDate, 1, 4)") == 0,
          "order and shipment numbers always carry the year of their date")
    return dict(prefix=prefix, before_order=before_order, w_prefix=word(len(prefix)), w_order=word(len(before_order)),
                w_both=word(len(flagged)))


@note("ch05.ex3", EXERCISES)
def ex3(d, claim):
    rows = d.q("SELECT substr(i.ItemCode, 5, 3), (CAST(substr(si.InvoiceDate, 6, 2) AS INTEGER) + 2) / 3, "
               "ROUND(SUM(l.LineTotal), 2), ROUND(SUM(l.Quantity), 2), COUNT(*), SUM(l.Quantity <> CAST(l.Quantity AS INTEGER)) "
               "FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
               "JOIN Item i ON i.ItemID = l.ItemID WHERE i.ItemGroup = 'Furniture' AND si.InvoiceDate BETWEEN ? AND ? "
               "GROUP BY 1, 2", f"{d.C}-07-01", f"{d.C}-12-31")
    grid: dict[str, dict[int, tuple[float, float]]] = {}
    lines = fractional = 0
    for code, qn, revenue, quantity, n, frac in rows:
        grid.setdefault(code, {})[qn] = (revenue, quantity)
        lines, fractional = lines + n, fractional + frac
    codes = sorted(grid)
    claim(codes == PRODUCT_TYPES, "the Furniture lines of Q3 and Q4 cover exactly the eight product types of Tutorial 5.1")
    get = lambda c, qn: grid[c].get(qn, (0.0, 0.0))
    total3, total4 = sum(get(c, 3)[0] for c in codes), sum(get(c, 4)[0] for c in codes)
    change = {c: get(c, 4)[0] - get(c, 3)[0] for c in codes}
    share = {c: get(c, 4)[0] / total4 - get(c, 3)[0] / total3 for c in codes}
    losers = sorted(codes, key=lambda c: change[c])[:2]
    gainers = sorted(codes, key=lambda c: -change[c])[:2]
    claim(set(losers) == {"NGT", "SDB"}, "nightstands and sideboards lost the most revenue")
    claim(set(gainers) == {"CON", "BKC"}, "consoles and bookcases gained the most revenue")
    largest = sorted(codes, key=lambda c: -abs(share[c]))[:4]
    claim(set(largest) == set(losers) | set(gainers) and all(share[c] < 0 for c in losers) and all(share[c] > 0 for c in gainers),
          "the four largest share changes are the two losers (down) and the two gainers (up)")
    claim(all(abs(s) <= 0.02 for s in share.values()), "no share changes by more than two points, so the threshold highlights none")
    claim(fractional > lines / 2, "quantities are fractional on most of the Furniture lines")
    shifts = [(c, f"{100 * share[c]:+.1f}") for c in sorted(losers, key=lambda c: share[c]) + sorted(gainers, key=lambda c: -share[c])]
    return dict(types=[(c, get(c, 3)[0], get(c, 4)[0], get(c, 3)[1], get(c, 4)[1]) for c in codes],
                total3=total3, total4=total4, shifts=shifts)


@note("ch05.ex4", EXERCISES)
def ex4(d, claim):
    rows = d.q("SELECT si.InvoiceDate, so.OrderDate FROM SalesInvoice si JOIN SalesOrder so ON so.SalesOrderID = si.SalesOrderID")
    claim(len(rows) == d.one("SELECT COUNT(*) FROM SalesInvoice"), "every invoice has its order")
    lag = [((date.fromisoformat(i[:10]) - date.fromisoformat(o[:10])).days, i) for i, o in rows]
    all_lags = [x for x, _ in lag]
    median, mean = statistics.median(all_lags), statistics.mean(all_lags)
    claim(mean > median, "the mean lag exceeds the median")
    claim(sum(x > mean for x in all_lags) < len(all_lags) / 2, "a minority of invoices take longer than the mean (right skew)")
    quarters = []
    for qn in range(1, 5):
        v = [x for x, i in lag if i[:4] == str(d.C) and quarter_of(i) == qn]
        quarters.append(dict(q=qn, invoices=len(v), mean=statistics.mean(v), median=days(statistics.median(v))))
    means = [qq["mean"] for qq in quarters]
    claim(max(means) - min(means) < 0.15 * mean, f"the average lag is stable across the quarters of {d.C} (within 15% of the mean)")
    promos = d.q("SELECT p.PromotionCode, p.EffectiveStartDate, p.EffectiveEndDate, SUM(si.InvoiceDate > p.EffectiveEndDate), "
                 "COUNT(*) FROM SalesInvoiceLine l JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                 "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID GROUP BY p.PromotionID ORDER BY p.PromotionID")
    every = [p for p in promos if p[3] == p[4]]
    wrong = [p for p in promos if p[2] <= p[1]]
    claim([p[0] for p in every] == [p[0] for p in wrong], "the promotions with every line after the end date are exactly those "
                                                          "whose end date is on or before their start date")
    claim(sum(p[2] == p[1] for p in every) == 1 and sum(p[2] < p[1] for p in every) == 2,
          "one of them is a one-day promotion and two end before they start")
    negative = sum(x < 0 for x in all_lags)
    return dict(invoices=len(rows), median=days(median), mean=mean, p90=days(percentile_inc(all_lags, 0.9)), quarters=quarters,
                promos=[(p[0], p[3], p[4]) for p in promos], every=series(p[0][-3:] for p in every),
                negative=word(negative).capitalize())


@note("ch05.ex5", EXERCISES)
def ex5(d, claim):
    matches = related_parties(d)
    claim(len({m[0] for m in matches}) == len(matches), "each matched supplier shares its address with one employee")
    standardized = d.q("SELECT s.SupplierID, e.EmployeeID FROM Supplier s JOIN Employee e "
                       "ON UPPER(TRIM(e.Address)) = UPPER(TRIM(s.Address)) AND UPPER(TRIM(e.City)) = UPPER(TRIM(s.City)) "
                       "ORDER BY 1, 2")
    claim(standardized == [(m[0], m[2]) for m in matches], "the addresses match exactly, so standardizing does not change the result")
    claim(anomalies(d, "related_party_address_match") == [m[0] for m in matches],
          "the matches are the AnomalyLog's related_party_address_match items")
    paid = {s: (n, a) for s, n, a in d.q("SELECT SupplierID, COUNT(*), ROUND(SUM(Amount), 2) FROM DisbursementPayment "
                                         "GROUP BY SupplierID")}
    return dict(n=word(len(matches)),
                matches=[dict(id=s, name=name, emp=e, emp_name=en, title=t, payments=paid.get(s, (0, 0.0))[0],
                              paid=paid.get(s, (0, 0.0))[1]) for s, name, e, en, t in matches])


@note("ch05.ex6", EXERCISES)
def ex6(d, claim):
    names = [r[0] for r in d.q("SELECT SupplierName FROM Supplier ORDER BY SupplierID")]
    changed = [(n, proper(n)) for n in names if proper(n) != n]
    words = {a for n, p in changed for a, b in zip(re.findall(r"[^\W\d_]+", n), re.findall(r"[^\W\d_]+", p)) if a != b}
    claim(all(w == "and" or w.isupper() for w in words),
          "the names are already consistently cased (PROPER changes only 'and' and capitalized abbreviations)")
    claim(all(e in names and proper(e) != e for e in PROPER_EXAMPLES), "the chapter's two examples are supplier names PROPER changes")
    claim(d.one("SELECT COUNT(*) FROM (SELECT TaxID FROM Supplier GROUP BY TaxID HAVING COUNT(*) > 1)") == 0 and
          d.one("SELECT COUNT(*) FROM (SELECT BankAccount FROM Supplier GROUP BY BankAccount HAVING COUNT(*) > 1)") == 0 and
          d.one("SELECT COUNT(*) FROM Supplier WHERE TaxID IS NULL OR BankAccount IS NULL") == 0,
          "no TaxID or BankAccount is shared")
    business = {s: (po, pay) for s, po, pay in d.q(
        "SELECT s.SupplierID, (SELECT COUNT(*) FROM PurchaseOrder p WHERE p.SupplierID = s.SupplierID), "
        "(SELECT COUNT(*) FROM DisbursementPayment p WHERE p.SupplierID = s.SupplierID) FROM Supplier s")}
    unapproved = [r[0] for r in d.q("SELECT SupplierID FROM Supplier WHERE IsApproved = 0 ORDER BY SupplierID")]
    claim(unapproved == list(range(unapproved[0], unapproved[-1] + 1)), "the unapproved suppliers have consecutive IDs")
    claim(all(business[s] == (0, 0) for s in unapproved), "no unapproved supplier has a purchase order or a payment")
    high = d.q("SELECT SupplierID, IsApproved FROM Supplier WHERE SupplierRiskRating = 'High' ORDER BY SupplierID")
    high_approved = [s for s, ok in high if ok == 1]
    claim(all(business[s][0] > 0 and business[s][1] > 0 for s in high_approved),
          "the approved High-risk suppliers are receiving business (purchase orders and payments)")
    conflict = d.q("SELECT ItemID, ItemCode FROM Item WHERE LifecycleStatus = 'Discontinued' AND IsActive = 1 ORDER BY ItemID")
    inactive = d.q("SELECT i.ItemID, i.ItemCode, i.LifecycleStatus, COUNT(*), MAX(si.InvoiceDate), "
                   "COUNT(DISTINCT CAST(substr(si.InvoiceDate, 1, 4) AS INTEGER)) FROM Item i "
                   "JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
                   "WHERE i.IsActive = 0 GROUP BY i.ItemID ORDER BY i.ItemID")
    claim(all(r[2] == "Discontinued" for r in inactive), "the inactive items still invoiced are all Discontinued")
    claim(all(r[5] == len(d.years) for r in inactive), "each of them was invoiced in every fiscal year")
    claim(len({r[4] for r in inactive}) == 1, "they share the same latest invoice date")
    claim(inactive[-1][1] == CHAPTER_SIDEBOARD and inactive[-1][1][4:7] == "SDB",
          "the last of them is the sideboard the chapter uses as an example")
    prelaunch = d.q("SELECT i.ItemID, i.ItemCode, i.LaunchDate, COUNT(*), MIN(si.InvoiceDate), MAX(si.InvoiceDate), "
                    "ROUND(SUM(l.LineTotal), 2) FROM Item i JOIN SalesInvoiceLine l ON l.ItemID = i.ItemID "
                    "JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID WHERE si.InvoiceDate < i.LaunchDate "
                    "GROUP BY i.ItemID ORDER BY i.ItemID")
    claim(anomalies(d, "item_status_alignment_conflict") == [r[0] for r in conflict],
          "the status conflicts are the AnomalyLog's item_status_alignment_conflict items")
    claim(anomalies(d, "discontinued_item_in_new_activity") == [r[0] for r in inactive],
          "the inactive items still invoiced are the AnomalyLog's discontinued_item_in_new_activity items")
    logged = anomalies(d, "prelaunch_item_in_new_activity")
    extra = [i for i in logged if i not in {r[0] for r in prelaunch}]
    claim({r[0] for r in prelaunch} <= set(logged) and len(extra) == 1,
          "the items invoiced before launch are among the AnomalyLog's prelaunch items, which name one item more")
    return dict(changed=len(changed), suppliers=len(names), examples=[(e, proper(e)) for e in PROPER_EXAMPLES],
                w_unapproved=word(len(unapproved)).capitalize(), unapproved_first=unapproved[0], unapproved_last=unapproved[-1],
                w_high=word(len(high)).capitalize(), high=series(s for s, _ in high), w_high_approved=word(len(high_approved)),
                w_related=word(len(related_parties(d))),
                w_conflict=word(len(conflict)), conflict_ids=", ".join(str(r[0]) for r in conflict),
                conflict_codes=", ".join(r[1] for r in conflict),
                w_inactive=word(len(inactive)).capitalize(), latest=inactive[0][4],
                inactive=[(r[1], r[3]) for r in inactive],
                w_prelaunch=word(len(prelaunch)).capitalize(),
                prelaunch=[dict(code=r[1], launch=r[2], lines=r[3], first=r[4], last=r[5]) for r in prelaunch],
                prelaunch_lines=sum(r[3] for r in prelaunch), prelaunch_amount=round(sum(r[6] for r in prelaunch), 2),
                extra=extra[0] if extra else None)
