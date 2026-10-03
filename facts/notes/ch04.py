"""Chapter 4's instructor notes: the values each note states, and the claims its wording makes."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from notes import note

EXERCISES = "chapters/04-excel-essentials/_exercises.qmd"
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]
BLANK_TRACKING = "(TrackingNumber IS NULL OR TrackingNumber = '')"


def xround(value: float, places: int = 2) -> float:
    """Round half away from zero, as Excel's ROUND does (the rule of scripts/figures/excel.py's xround)."""
    text = repr(float(f"{value:.15g}"))
    return float(Decimal(text).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def anomalies(d, kind: str) -> set | None:
    """The primary keys the generator's AnomalyLog lists for an anomaly type; None if there is no
    support workbook beside the dataset."""
    keys = d.anomalies(kind)
    return None if keys is None else set(keys)


@note("ch04.ex1", EXERCISES)
def ex1(d, claim):
    by_year = {int(y): r for y, *r in d.q(
        "SELECT substr(InvoiceDate, 1, 4), COUNT(*), ROUND(SUM(SubTotal), 2), ROUND(SUM(FreightAmount), 2), "
        "ROUND(SUM(TaxAmount), 2), ROUND(SUM(GrandTotal), 2) FROM SalesInvoice GROUP BY 1")}
    invoices, subtotal = d.q("SELECT COUNT(*), ROUND(SUM(SubTotal), 2) FROM SalesInvoice")[0]
    claim(set(by_year) == set(d.years), "the invoices fall in the fiscal years of the window, so the grid's total row "
                                        "equals the totals of the entire SalesInvoice Table")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoice WHERE ABS(SubTotal + FreightAmount + TaxAmount - GrandTotal) > 0.005") == 0,
          "SubTotal + Freight + Tax = GrandTotal on every invoice")
    memos = {int(y): (n, s) for y, n, s in d.q(
        "SELECT substr(CreditMemoDate, 1, 4), COUNT(*), ROUND(SUM(SubTotal), 2) FROM CreditMemo GROUP BY 1")}
    claim(set(memos) <= set(d.years), "the credit memos fall in the fiscal years of the window")
    posted = dict((n, (t, b)) for n, t, b in d.q(
        "SELECT a.AccountNumber, a.AccountType, ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g "
        "JOIN Account a ON a.AccountID = g.AccountID WHERE g.SourceDocumentType = 'SalesInvoice' GROUP BY 1, 2"))
    freight, tax = d.one("SELECT ROUND(SUM(FreightAmount), 2) FROM SalesInvoice"), d.one("SELECT ROUND(SUM(TaxAmount), 2) FROM SalesInvoice")
    freight_type, freight_posted = posted.get(4050, (None, 0.0))
    claim(freight_type == "Revenue" and abs(freight_posted - freight) < 0.005,
          "the freight billed on the invoices is credited to its own revenue account, 4050")
    claim(any(t == "Liability" and abs(b - tax) < 0.005 for t, b in posted.values()),
          "the sales tax on the invoices is credited to a liability account")
    years = d.years
    return dict(years=years, n=[by_year[y][0] for y in years], invoices=invoices, sub=[by_year[y][1] for y in years],
                sub_total=subtotal, frt=[by_year[y][2] for y in years], tax=[by_year[y][3] for y in years],
                gt=[by_year[y][4] for y in years], cm_n=[memos.get(y, (0, 0.0))[0] for y in years],
                cm_sub=[memos.get(y, (0, 0.0))[1] for y in years])


@note("ch04.ex2", EXERCISES)
def ex2(d, claim):
    programs = d.q("SELECT PromotionID, PromotionName, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram "
                   "ORDER BY PromotionID")
    lines = d.q("SELECT PromotionID, Quantity, UnitPrice, Discount, LineTotal FROM SalesInvoiceLine WHERE PromotionID IS NOT NULL")
    claim(all(name.endswith(" Promotion") for _, name, _, _ in programs), "every PromotionName ends with \"Promotion\"")
    promos = []
    for pid, name, _, _ in programs:
        mine = [r for r in lines if r[0] == pid]
        promos.append(dict(id=pid, name=name.removesuffix(" Promotion"), lines=len(mine),
                           total=round(sum(r[4] for r in mine), 2),
                           discount=round(sum(xround(r[1] * r[2] * r[3]) for r in mine), 2)))
    discount = round(sum(p["discount"] for p in promos), 2)
    top = max(promos, key=lambda p: p["discount"])
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                "WHERE ABS(l.Discount - p.DiscountPct) > 1e-9") == 0, "every promotion line carries its promotion's DiscountPct")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine WHERE Discount <> 0 AND PromotionID IS NULL") == 0,
          "no line has a discount without a PromotionID")
    claim(d.one("SELECT COUNT(*) FROM SalesInvoiceLine l LEFT JOIN PromotionProgram p ON p.PromotionID = l.PromotionID "
                "WHERE l.PromotionID IS NOT NULL AND p.PromotionID IS NULL") == 0,
          "every promotion line's PromotionID is in the PromotionProgram Table")
    backwards = [pid for pid, _, start, end in programs if end < start]
    single = [pid for pid, _, start, end in programs if end == start]
    claim(len(backwards) >= 2, "two or more promotions have an EffectiveEndDate earlier than their EffectiveStartDate")
    claim(len(single) == 1, "one promotion is effective for a single day")
    return dict(promos=promos, lines=len(lines), discount=discount,
                top=dict(id=top["id"], share=top["discount"] / discount), backwards=backwards, single=single)


@note("ch04.ex3", EXERCISES)
def ex3(d, claim):
    items = d.q("SELECT ItemGroup, ListPrice - StandardCost, (ListPrice - StandardCost) / ListPrice FROM Item "
                "WHERE ListPrice IS NOT NULL AND ItemType = 'Finished Good'")
    names = sorted({r[0] for r in items})
    claim(names == ["Accessories", "Furniture", "Lighting", "Textiles"], "the finished goods are in the four product groups "
                                                                         "the exercise's list offers")
    services = d.q("SELECT ItemGroup, ItemType, StandardCost FROM Item WHERE ListPrice IS NOT NULL AND ItemType <> 'Finished Good'")
    claim(all(g == "Services" for g, _, _ in services), "the only items with a list price that are not finished goods "
                                                        "are the design services")
    claim(services and all(c == 0 for _, _, c in services), "the design services have a StandardCost of 0")
    claim(d.one("SELECT COUNT(*) FROM Item WHERE ItemType = 'Finished Good' AND ListPrice IS NULL") == 0,
          "every finished good has a list price, so the Item Table of Tutorial 4.1 holds them all")
    groups = []
    for g in names:
        mine = [r for r in items if r[0] == g]
        groups.append(dict(name=g, margin=sum(r[1] for r in mine) / len(mine), pct=sum(r[2] for r in mine) / len(mine),
                           below=sum(1 for r in mine if r[2] < 0.45)))
    low, high = min(r[2] for r in items), max(r[2] for r in items)
    claim(low >= 0.30, "no item is below 30 percent")
    top = max(groups, key=lambda g: g["margin"])
    claim(top is min(groups, key=lambda g: g["pct"]), f"{top['name']}, which earns the most per unit, has the lowest "
                                                      "average percentage")
    method = d.q("SELECT COUNT(*), SUM(PricingMethod LIKE '%Price List' AND UnitPrice < BaseListPrice - 0.005), "
                 "SUM(Discount > 0) FROM SalesInvoiceLine")[0]
    claim(method[1] > method[0] / 2, "most sales are billed at price-list prices below list")
    claim(0 < method[2] < method[0] / 2, "some (not most) sales carry promotional discounts")
    return dict(items=len(items), services=WORDS[len(services)], groups=groups, low=low, high=high,
                below=sum(g["below"] for g in groups),
                below_by=[(g["name"], g["below"]) for g in sorted(groups, key=lambda g: (-g["below"], g["name"]))],
                top_group=top["name"])


@note("ch04.ex4", EXERCISES)
def ex4(d, claim):
    rows = d.q("SELECT o.FreightTerms, s.FreightCost, s.BillableFreightAmount FROM Shipment s "
               "LEFT JOIN SalesOrder o ON o.SalesOrderID = s.SalesOrderID")
    terms = {t for t, _, _ in rows}
    claim(terms == {"Prepaid", "Prepaid and Add"}, "the FreightTerms values are Prepaid and Prepaid and Add "
                                                   "(every shipment's sales order is found)")

    def summary(term):
        mine = [r for r in rows if r[0] == term]
        diff = [round(b - c, 2) for _, c, b in mine]
        return dict(n=len(mine), margin=round(sum(b - c for _, c, b in mine), 2),
                    avg_cost=sum(c for _, c, _ in mine) / len(mine),
                    above=sum(x > 0 for x in diff), below=sum(x < 0 for x in diff), equal=sum(x == 0 for x in diff),
                    ratio=sum(b / c for _, c, b in mine) / len(mine),
                    recovered=sum(b for _, _, b in mine) / sum(c for _, c, _ in mine),
                    billed_max=max(b for _, _, b in mine), cost_min=min(c for _, c, _ in mine))

    pp, pa = summary("Prepaid"), summary("Prepaid and Add")
    claim(pp["billed_max"] == 0 and pp["cost_min"] > 0, "every Prepaid shipment has BillableFreightAmount 0 and a "
                                                        "freight cost, so all are negative")
    claim(0.5 < pa["recovered"] < 1, "freight billed under Prepaid and Add recovers most but not all of the carrier cost")
    claim(pa["above"] > 0 and pa["below"] > 0, "Prepaid and Add shipments bill freight both above and below cost")
    return dict(shipments=len(rows), pp=pp, pa=pa, margin=round(sum(b - c for _, c, b in rows), 2),
                negative=sum(round(b - c, 2) < 0 for _, c, b in rows),
                low=min(c for _, c, _ in rows), high=max(c for _, c, _ in rows))


@note("ch04.ex5", EXERCISES)
def ex5(d, claim):
    review, review2 = f"{d.C}-12-31", f"{d.C}-12-01"
    shipments = d.one("SELECT COUNT(*) FROM Shipment")
    statuses = {s for (s,) in d.q("SELECT DISTINCT Status FROM Shipment")}
    claim(statuses == {"Delivered", "In Transit"}, "the shipment statuses are Delivered and In Transit")
    blank = dict(d.q(f"SELECT Status, COUNT(*) FROM Shipment WHERE {BLANK_TRACKING} GROUP BY 1"))
    by_year = {int(y): n for y, n in d.q("SELECT substr(ShipmentDate, 1, 4), COUNT(*) FROM Shipment "
                                         "WHERE Status = 'In Transit' GROUP BY 1")}
    transit = sum(by_year.values())
    claim(set(by_year) == set(d.years), "the In Transit shipments come from every year of the data, and only from them")
    late = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review)
    late2 = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate < ?", review2)
    on_review = d.one("SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND DeliveryDate = ?", review)
    claim(transit - late == 1 and on_review == 1, "of the In Transit shipments, all but one are due before the review "
                                                  "date, and the other is due on the review date itself")
    claim(d.one(f"SELECT COUNT(*) FROM Shipment WHERE Status = 'In Transit' AND {BLANK_TRACKING} AND DeliveryDate < ?",
                review) == blank.get("In Transit", 0) > 0,
          "all In Transit shipments with a blank tracking number are in both categories")
    claim(d.one("SELECT COUNT(*) FROM Shipment WHERE ShipmentDate IS NULL OR ShipmentDate = '' OR DeliveryDate IS NULL "
                "OR DeliveryDate = ''") == 0, "no ShipmentDate or DeliveryDate is blank")
    return dict(shipments=shipments, blank=sum(blank.values()), blank_delivered=blank.get("Delivered", 0),
                blank_transit=blank.get("In Transit", 0), transit=transit,
                transit_by_year=[(y, by_year[y]) for y in d.years], review=review, review2=review2,
                late=late, late2=late2)


@note("ch04.ex6", EXERCISES)
def ex6(d, claim):
    rows = d.q("SELECT PriceOverrideApprovalID, SalesOrderLineID, RequestedByEmployeeID, ApprovedByEmployeeID, ApprovedDate, "
               "Status, 1 - ApprovedUnitPrice / ReferenceUnitPrice, ApprovedUnitPrice FROM PriceOverrideApproval "
               "ORDER BY PriceOverrideApprovalID")
    claim({r[5] for r in rows} == {"Approved", "Pending"}, "the request statuses are Approved and Pending")
    approved = [r for r in rows if r[5] == "Approved"]
    pending = [r for r in rows if r[5] == "Pending"]
    approvers = {r[3] for r in approved}
    claim(len(approvers) == 1 and None not in approvers, "all approvals were made by one employee")
    approver = approvers.pop()
    name, title = d.q("SELECT EmployeeName, JobTitle FROM Employee WHERE EmployeeID = ?", approver)[0]
    claim(all(r[3] is None and r[4] is None for r in pending), "the Pending requests have no approver or approval date")
    own = [r for r in rows if r[2] == approver]
    self_approved = sum(1 for r in own if r[3] == approver)
    claim([r[0] for r in own if r[3] != approver] == [r[0] for r in pending],
          "the approver's other requests are exactly the Pending ones")
    claim(len(pending) >= 2, "there are two or more Pending requests (the list of IDs is plural)")
    requesters = sorted({r[2] for r in rows})
    claim(approver in requesters, "the only approver is also a requester")
    claim(anomalies(d, "missing_price_override_approval") == {r[0] for r in pending},
          "the Pending requests are the AnomalyLog's missing_price_override_approval items")
    claim(anomalies(d, "sale_below_price_floor_without_approval") == {r[1] for r in pending},
          "the Pending requests' sales order lines are the AnomalyLog's sale_below_price_floor_without_approval items")
    billed = {}
    for r in pending:
        billed[r[0]] = d.q("SELECT UnitPrice, PricingMethod FROM SalesInvoiceLine WHERE SalesOrderLineID = ?", r[1])
    claim(all(billed[r[0]] and all(abs(u - r[7]) < 0.005 and m.endswith("Price List") for u, m in billed[r[0]])
              for r in pending),
          "the Pending requests' sales order lines were invoiced at the pending ApprovedUnitPrice under a price-list "
          "PricingMethod")
    return dict(requests=len(rows), approved=len(approved), pending=len(pending), pending_word=WORDS[len(pending)],
                approver=dict(id=approver, name=name, title=title),
                by_requester=[(e, sum(1 for r in rows if r[2] == e)) for e in requesters],
                self_approved=self_approved, own=len(own), ids=[r[0] for r in pending], lines=[r[1] for r in pending],
                low=min(r[6] for r in rows), high=max(r[6] for r in rows))
