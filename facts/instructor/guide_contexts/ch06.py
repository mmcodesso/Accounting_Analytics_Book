"""Chapter 6's instructor guides: the values the guides state, and the claims their wording makes.

Chapter 6 is the third Excel chapter (statistical functions, conditional aggregation and control totals, PivotTables with
calculated fields, a trial balance and income statement built from the ledger, and a margin bridge), so the contexts do
three jobs, as in Chapters 4 and 5:

- they supply the values the tutorials' checkpoints and each exercise's model answer show (the Profile worksheet, the
  Drivers and Bridge worksheets, the cells of the exercise sheets),
- they give the layout the solution workbook uses where a step names a cell or a column letter (the TrialBalance Table),
- they check, with claim(), every table and column the guides name and every statement about the data that another
  dataset could falsify, so a roll or a schema change flags the wording instead of leaving it stale.

Keys: ch06.chapter (the chapter note and its three tutorials) and ch06.g1 to ch06.g6 (the exercises; each is used next to
the registered note ch06.ex1 to ch06.ex6 that supplies the values of the exercise's instructor note).
The model answers are in outputs/companion/solutions/Chapter06-exercises (Chapter 6 Exercises - Solutions.xlsx).
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path

from guide_contexts import context
from guide_contexts.ch01 import and_join, schema
from guide_contexts.ch03 import col_letter
from guide_contexts.ch04 import excel_percentile, long_date
from notes.ch06 import GROUPS, TYPE_NAMES, lines, total

REPO = Path(__file__).resolve().parents[3]
CHAPTER = REPO / "chapters" / "06-descriptive-analytics"
DECK = REPO / "slides" / "chapter-06" / "index.qmd"
PRODUCTS = [g for g in GROUPS if g != "Services"]
# the TrialBalance Table of Exercise 6.1, in the order the query and the three calculated columns leave it
TB_COLUMNS = ["AccountID", "Debit", "Credit", "AccountNumber", "AccountName", "AccountType", "AccountSubType",
              "Balance", "DebitBalance", "CreditBalance"]
THRESHOLD_PERCENTILE = 0.9          # Parameters!B3, the percentile Tutorial 6.1's 90th-percentile cell reads


# --- helpers -------------------------------------------------------------------------------------------------------

def slide_count() -> int:
    """The slides of the chapter's deck: the title slide plus one per # or ## heading."""
    return 1 + sum(1 for line in DECK.read_text(encoding="utf-8").splitlines() if re.match(r"^#{1,2} ", line))


def exercise_counts() -> dict[str, int]:
    persp, current, counts = {"Financial": "financial", "Managerial": "managerial", "Auditing": "auditing"}, None, {}
    for line in (CHAPTER / "_exercises.qmd").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (Financial|Managerial|Auditing) ", line)
        if m:
            current = persp[m.group(1)]
        elif re.match(r"^\*\*Exercise \d+\.\d+", line):
            counts[current] = counts.get(current, 0) + 1
    return counts


def mcq_facts() -> tuple[int, list[int]]:
    """The number of multiple-choice questions, and the questions whose correct option is also the longest."""
    import source
    text = (CHAPTER / "_multiple-choice.qmd").read_text(encoding="utf-8")
    comment = source.note_comment("chapters/06-descriptive-analytics/_multiple-choice.qmd", "mcq",
                                  r"<!--\s*Answer key, (?:Chapter|Appendix) 6\b")
    key = {int(n): a for n, a in re.findall(r"(\d+) ([A-D])[,.]", comment.split("\n", 2)[1])}
    longest = []
    for n, body in re.findall(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|\Z)", text, re.M | re.S):
        options = dict(re.findall(r"^([A-D])\.  (.+)$", body, re.M))
        if options and int(n) in key:
            sizes = sorted((len(v), o) for o, v in options.items())
            if sizes[-1][1] == key[int(n)] and sizes[-1][0] > sizes[-2][0]:
                longest.append(int(n))
    return len(re.findall(r"^\*\*\d+\.\*\*", text, re.M)), longest


def group_quarter(rows) -> dict:
    """(item group, quarter) -> [revenue, standard cost] of the invoice lines."""
    out: dict = {}
    for r in rows:
        a = out.setdefault((r["grp"], r["q"]), [0.0, 0.0])
        a[0] += r["R"]
        a[1] += r["C"]
    return out


def furniture_bridge(d) -> dict:
    """Tutorial 6.3's Drivers and Bridge worksheets: the Furniture totals of the third and fourth quarters, the per-unit
    measures, the four effects (cost is zero by construction), and the discounts by promotion."""
    rows = [r for r in lines(d, d.C) if r["grp"] == "Furniture" and r["q"] in (3, 4)]
    a = {}
    for q in (3, 4):
        part = [r for r in rows if r["q"] == q]
        a[q] = {k: sum(r[k] for r in part) for k in ("U", "R", "C", "D", "L")}
        x = a[q]
        x.update(M=x["R"] - x["C"], m=(x["R"] - x["C"]) / x["U"], lm=(x["L"] - x["C"]) / x["U"],
                 k=(x["L"] - x["R"] - x["D"]) / x["U"], dd=x["D"] / x["U"], price=x["R"] / x["U"], listp=x["L"] / x["U"],
                 costp=x["C"] / x["U"], margin_pct=(x["R"] - x["C"]) / x["R"],
                 mbd=(x["R"] + x["D"] - x["C"]) / (x["R"] + x["D"]))
    x3, x4 = a[3], a[4]
    effects = dict(volume=(x4["U"] - x3["U"]) * x3["m"], mix=x4["U"] * (x4["lm"] - x3["lm"]),
                   price_lists=-x4["U"] * (x4["k"] - x3["k"]), promotions=-x4["U"] * (x4["dd"] - x3["dd"]), cost=0.0)
    change = x4["M"] - x3["M"]
    check = x3["M"] + sum(effects.values()) - x4["M"]
    promos: dict = {}
    for r in rows:
        if r["promo"] is not None:
            p = promos.setdefault(r["promo"], {3: [0, 0.0], 4: [0, 0.0]})
            p[r["q"]][0] += 1
            p[r["q"]][1] += r["D"]
    blank = {q: sum(1 for r in rows if r["q"] == q and r["promo"] is None) for q in (3, 4)}
    return dict(q3=x3, q4=x4, effects=effects, change=change, check=check, promos=promos, blank=blank)


# --- the chapter note and its tutorials ----------------------------------------------------------------------------------

CHAPTER_SCHEMA = {
    "SalesInvoice": ["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID"],
    "SalesInvoiceLine": ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount",
                         "LineTotal", "PromotionID", "PricingMethod"],
    "Item": ["ItemID", "ItemCode", "ItemName", "ItemGroup", "StandardCost", "ListPrice", "UnitOfMeasure"],
    "Customer": ["CustomerID", "CustomerName", "CustomerSegment", "Region"],
    "PromotionProgram": ["PromotionID", "PromotionName", "ItemGroup", "DiscountPct", "EffectiveStartDate", "EffectiveEndDate"],
    "GLEntry": ["PostingDate", "VoucherNumber", "AccountID", "Debit", "Credit"],
    "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
    "JournalEntry": ["EntryNumber", "EntryType", "PostingDate", "TotalAmount"],
}


@context("ch06.chapter")
def chapter(d, claim):
    schema(d, claim, CHAPTER_SCHEMA)
    y, p = d.C, d.P
    rows = lines(d, y)
    prior = lines(d, p)

    # Tutorial 6.1: the Profile worksheet
    values = sorted(r["R"] for r in rows)
    n, revenue = len(values), sum(values)
    mean, median, stdev = statistics.mean(values), statistics.median(values), statistics.stdev(values)
    p90 = excel_percentile(values, THRESHOLD_PERCENTILE)
    big = max(rows, key=lambda r: r["R"])
    small = min(rows, key=lambda r: r["R"])
    big_name = d.one("SELECT ItemName FROM Item WHERE ItemCode = ?", big["code"])
    claim(big["grp"] == "Services" and big["uom"] == "Hour", "the largest line of the year is an hourly design service, not a product")
    claim(small["R"] < 2, "the smallest line of the year is under two dollars")
    claim(1.3 < mean / median < 1.7, "the average line is about half again as large as the median line")
    claim(0.8 < stdev / mean < 1.1, "the standard deviation is almost as large as the average")
    top_share = sum(v for v in values if v > p90) / revenue
    claim(0.25 < top_share < 0.35, "the lines above the 90th percentile carry nearly a third of the year's revenue")
    group_rows = []
    for g in GROUPS:
        v = [r["R"] for r in rows if r["grp"] == g]
        group_rows.append(dict(group=g, lines=len(v), revenue=sum(v), average=statistics.mean(v)))
    products = group_rows[:-1]
    services = group_rows[-1]
    claim(len(group_rows) == 5 and d.one("SELECT COUNT(DISTINCT ItemGroup) FROM Item WHERE ListPrice IS NOT NULL") == 5,
          "the Item Table (the items with a list price) has five item groups, four product lines and Services, so the controller's list of four leaves one out")
    claim(abs(sum(x["revenue"] for x in products) + services["revenue"] - revenue) < 0.005, "the five groups add up to the year's revenue")
    bins = [sum(1 for v in values if lo <= v < lo + 1000) for lo in range(0, 15000, 1000)] + [sum(1 for v in values if v >= 15000)]
    claim(bins[0] == max(bins) and bins[-1] > bins[-2] and bins[-1] > bins[-3] and sum(bins) == n,
          "the first bin of the histogram is the tallest, the open-ended last bin is taller than the two before it, and the bins add up to the year's lines")
    claim(all(bins[i] >= bins[i + 1] for i in range(0, 13)), "the bin counts fall at every step from the first bin to the 14,000 bin")
    t1 = dict(lines=n, revenue=revenue, mean=mean, median=median, stdev=stdev, smallest=small["R"], largest=big["R"], p90=p90,
              big_code=big["code"], big_name=big_name, big_hours=big["U"], small_qty=small["U"], ratio=mean / median, spread=stdev / mean,
              top_share=top_share, groups=group_rows, product_lines=sum(x["lines"] for x in products),
              product_revenue=sum(x["revenue"] for x in products), bins=bins, bin_max=max(bins), last_bin=bins[-1], n_bins=len(bins),
              prior_lines=len(prior), prior_revenue=sum(r["R"] for r in prior))

    # Tutorial 6.2: revenue and margin by item group and quarter, and the segments
    gq = group_quarter(rows)
    margin = {(g, k): 1 - gq[(g, k)][1] / gq[(g, k)][0] for g in GROUPS for k in range(1, 5)}
    claim(all(margin[("Furniture", k)] < min(margin[(g, k)] for g in PRODUCTS if g != "Furniture") for k in range(1, 5)),
          "the Furniture margin is lower than that of the other product lines in every quarter")
    claim(margin[("Furniture", 4)] < margin[("Furniture", 3)] - 0.01, "the Furniture margin falls by more than a point from the third quarter to the fourth")
    steady = max(max(margin[(g, k)] for k in range(1, 5)) - min(margin[(g, k)] for g in [g] for k in range(1, 5))
                 for g in PRODUCTS if g != "Furniture")
    claim(steady < 0.01, "the margins of Lighting, Textiles and Accessories move by less than a point across the four quarters")
    claim(all(margin[("Services", k)] == 1 for k in range(1, 5)) and all(r["std"] == 0 for r in rows if r["grp"] == "Services"),
          "Services shows a margin of 100 percent because its items carry a standard cost of 0")
    rev = {(g, k): gq[(g, k)][0] for g in GROUPS for k in range(1, 5)}
    col = {k: sum(rev[(g, k)] for g in GROUPS) for k in range(1, 5)}
    share3, share4 = rev[("Furniture", 3)] / col[3], rev[("Furniture", 4)] / col[4]
    claim(share4 < share3, "Furniture's share of the quarter's revenue falls from the third quarter to the fourth")
    claim(rev[("Lighting", 4)] < rev[("Lighting", 3)] and abs(margin[("Lighting", 4)] - margin[("Lighting", 3)]) < 0.005,
          "Lighting's revenue falls from the third quarter to the fourth while its margin does not")
    seg = {}
    for r in prior + rows:
        seg.setdefault(r["segment"], [0.0, 0.0])[0 if r in prior else 1] += r["R"]
    seg_rows = sorted(({"segment": s, "prior": v[0], "now": v[1], "change": v[1] / v[0] - 1} for s, v in seg.items()), key=lambda t: -t["now"])
    claim(seg_rows[0]["segment"] == "Wholesale" and 0.45 < seg_rows[0]["now"] / revenue < 0.55 and seg_rows[0]["change"] > 0,
          "Wholesale is the largest segment, with about half of the year's revenue, and it grew from the previous year")
    by_seg = {s["segment"]: s["change"] for s in seg_rows}
    claim(by_seg["Strategic"] < 0 and by_seg["Design Trade"] < 0 and by_seg["Small Business"] > 0,
          "the Strategic and Design Trade segments declined and Small Business grew from the previous year")
    total_change = revenue / sum(r["R"] for r in prior) - 1
    claim(0 < total_change < 0.02, "total revenue rose by about one percent")
    t2 = dict(margin_q=[[margin[(g, k)] for k in range(1, 5)] for g in GROUPS], revenue_q=[[rev[(g, k)] for k in range(1, 5)] for g in GROUPS],
              share3=share3, share4=share4, furniture_change=rev[("Furniture", 4)] / rev[("Furniture", 3)] - 1,
              lighting_change=rev[("Lighting", 4)] / rev[("Lighting", 3)] - 1, steady=steady, segments=seg_rows, total_change=total_change,
              wholesale_share=seg_rows[0]["now"] / revenue, groups=GROUPS)

    # Tutorial 6.3: the drivers, the bridge and the discounts by promotion
    fb = furniture_bridge(d)
    x3, x4, ef = fb["q3"], fb["q4"], fb["effects"]
    base_ok = d.one("SELECT COUNT(*) FROM SalesInvoiceLine l JOIN Item i ON i.ItemID = l.ItemID WHERE l.BaseListPrice <> i.ListPrice") == 0
    claim(base_ok, "BaseListPrice equals the item's ListPrice on every invoice line, so list margin per unit moves only with mix")
    claim(abs(fb["check"]) < 1e-6, "the volume, mix, price-list, promotion and cost effects add up exactly to the change in the Furniture margin")
    claim(abs(x4["U"] / x3["U"] - 1) < 0.01 and abs(x4["listp"] / x3["listp"] - 1) < 0.01 and abs(x4["costp"] / x3["costp"] - 1) < 0.015,
          "the quantity, the list price per unit and the standard cost per unit of Furniture barely change from the third quarter to the fourth")
    claim(x4["D"] > 2 * x3["D"], "the promotional discounts on Furniture more than double from the third quarter to the fourth")
    claim(x4["price"] < x3["price"], "the price per unit of Furniture falls from the third quarter to the fourth")
    claim(x4["mbd"] > x3["mbd"], "the Furniture margin before discounts rises from the third quarter to the fourth")
    claim(ef["promotions"] < fb["change"] < 0, "the promotions effect is a loss larger than the whole decline in the Furniture margin")
    claim(all(abs(ef[k]) < 0.1 * abs(fb["change"]) for k in ("volume", "mix", "price_lists")), "the volume, mix and price-list effects are each under a tenth of the decline")
    claim(0 < ef["promotions"] + (x4["D"] - x3["D"]) < 0.01 * (x4["D"] - x3["D"]), "the promotions effect is slightly smaller than the increase in discount dollars")
    promos = fb["promos"]
    main = max(promos, key=lambda k: promos[k][3][1] + promos[k][4][1])
    claim(all(promos[main][q][1] > 0.9 * x["D"] for q, x in ((3, x3), (4, x4))), f"promotion {main} supplies more than nine-tenths of the Furniture discounts in both quarters")
    nine = [k for k in promos if k != main and promos[k][3][1] == 0 and promos[k][4][1] > 0]
    claim(len(nine) == 1, "one other promotion adds Furniture discounts in the fourth quarter only")
    promo_name = {k: n for k, n in d.q("SELECT PromotionID, PromotionName FROM PromotionProgram")}
    start, end = d.q("SELECT EffectiveStartDate, EffectiveEndDate FROM PromotionProgram WHERE PromotionID = ?", main)[0]
    t3 = dict(q3=x3, q4=x4, effects=ef, change=fb["change"], disc_up=x4["D"] - x3["D"], disc_ratio=x4["D"] / x3["D"], promos=promos, blank=fb["blank"],
              main=main, main_name=promo_name[main], main_start=long_date(start), main_end=long_date(end), nine=nine[0], nine_name=promo_name[nine[0]],
              promo_ids=sorted(promos), margin_drop_pts=100 * (x3["margin_pct"] - x4["margin_pct"]))

    ex = exercise_counts()
    claim(ex == {"financial": 2, "managerial": 2, "auditing": 2}, "the exercises are two for each of the three perspectives")
    n_q, longest = mcq_facts()
    return dict(y=y, p=p, lines_all=d.one("SELECT COUNT(*) FROM SalesInvoiceLine"), n_exercises=sum(ex.values()), per_perspective=ex.get("financial", 0), slides=slide_count(), n_questions=n_q,
                longest_correct=and_join(longest), n_longest=len(longest), t1=t1, t2=t2, t3=t3)


# --- Exercise 6.1: from the ledger to the income statement ----------------------------------------------------------------

@context("ch06.g1")
def g1(d, claim):
    schema(d, claim, {"GLEntry": ["PostingDate", "VoucherNumber", "AccountID", "Debit", "Credit"],
                      "Account": ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType"],
                      "JournalEntry": ["EntryNumber", "EntryType", "TotalAmount"]})
    y = d.C
    c1, c2 = d.closes_of(y)
    rows_all = d.one("SELECT COUNT(*) FROM GLEntry")
    rows_next = d.one("SELECT COUNT(*) FROM GLEntry WHERE PostingDate >= ?", f"{d.N}-01-01")
    rows_close = d.one("SELECT COUNT(*) FROM GLEntry WHERE VoucherNumber IN (?, ?)", c1, c2)
    claim(rows_next > 0 and d.one("SELECT COUNT(DISTINCT SourceDocumentType) FROM GLEntry WHERE PostingDate >= ?", f"{d.N}-01-01") == 1
          and d.one("SELECT SourceDocumentType FROM GLEntry WHERE PostingDate >= ? LIMIT 1", f"{d.N}-01-01") == "DisbursementPayment",
          f"the ledger holds rows dated after the fiscal year-end, and they are all supplier payments (DisbursementPayment)")
    all_dr, all_cr = d.q("SELECT ROUND(SUM(Debit), 2), ROUND(SUM(Credit), 2) FROM GLEntry")[0]
    claim(abs(all_dr - all_cr) < 0.005, "the ledger balances without the date filter, so equal debit and credit balances cannot reveal the missing filter")
    cash = d.account("1010")
    cash_bal = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND PostingDate < ? AND VoucherNumber NOT IN (?, ?)",
                     cash, f"{d.N}-01-01", c1, c2)
    cash_all = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND VoucherNumber NOT IN (?, ?)", cash, c1, c2)
    claim(cash_all < cash_bal, "without the date filter the cash balance falls, because the later supplier payments credit cash")
    claim(d.one("SELECT COUNT(*) FROM Account") > 71, "the chart of accounts has accounts that the trial balance leaves out (no postings in the period)")
    cogs = d.q("SELECT a.AccountNumber, a.AccountName, ROUND(SUM(g.Debit) - SUM(g.Credit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID "
               "WHERE a.AccountSubType = 'COGS' AND g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?) GROUP BY a.AccountID HAVING ROUND(SUM(g.Debit) - SUM(g.Credit), 2) <> 0 "
               "ORDER BY a.AccountNumber", f"{d.N}-01-01", c1, c2)
    claim({str(r[0]) for r in cogs} >= {"5010", "5050", "5060", "5080"}, "the COGS subtype holds accounts 5010, 5050, 5060 and 5080 with balances")
    claim(d.one("SELECT COUNT(*) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = 4070") == 0,
          "account 4070 Sales Discounts has no postings, so it adds no line to the income statement")
    kept = rows_all - rows_next - rows_close
    names = {n: (nm, ty, sub) for n, nm, ty, sub in d.q("SELECT AccountNumber, AccountName, AccountType, AccountSubType FROM Account WHERE AccountNumber IN (4050, 4060, 7020, 7030)")}
    claim(names.get(4050, ("",))[0] == "Freight Revenue" and names.get(4060, ("",))[0] == "Sales Returns and Allowances"
          and names.get(7020, ("", "", ""))[1:] == ("Revenue", "Other Income or Expense") and names.get(7030, ("", "", ""))[1:] == ("Expense", "Other Expense"),
          "account 4050 is Freight Revenue, 4060 Sales Returns and Allowances, 7020 is typed Revenue with the subtype Other Income or Expense, and 7030 is Other Expense")
    zero_accounts = [r[0] for r in d.q("SELECT a.AccountNumber FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?) "
                                       "GROUP BY a.AccountID HAVING ROUND(SUM(g.Debit) - SUM(g.Credit), 2) = 0 ORDER BY a.AccountNumber", f"{d.N}-01-01", c1, c2)]
    claim(d.closes_of(d.P) and d.closes_of(d.F), "the closing entries of the earlier years are in the ledger")
    # the delivery evidence of the cutoff invoices (invoices numbered in the report year but dated in the year before)
    schema(d, claim, {"CreditMemo": ["CreditMemoDate", "SubTotal", "FreightCreditAmount"], "Shipment": ["ShipmentDate", "DeliveryDate"],
                      "ShipmentLine": ["ShipmentLineID", "ShipmentID"]})
    deliveries = []
    for sid, number in d.q("SELECT SalesInvoiceID, InvoiceNumber FROM SalesInvoice WHERE InvoiceDate < ? AND InvoiceNumber LIKE ? ORDER BY InvoiceNumber",
                           f"{y}-01-01", f"SI-{y}-%"):
        got = d.q("SELECT DISTINCT s.ShipmentDate, s.DeliveryDate FROM SalesInvoiceLine l JOIN ShipmentLine sl ON sl.ShipmentLineID = l.ShipmentLineID "
                  "JOIN Shipment s ON s.ShipmentID = sl.ShipmentID WHERE l.SalesInvoiceID = ? ORDER BY 1, 2", sid)
        claim(len(got) > 0 and all(sh and dl and sh <= dl and sh[:4] == dl[:4] for sh, dl in got),
              f"{number} has shipments with a delivery date on or after the shipment date, in the same year")
        deliveries.append(dict(number=number, shipped=sorted({sh for sh, _ in got}), delivered=sorted({dl for _, dl in got}),
                               shipped_year=min(sh for sh, _ in got)[:4]))
    claim(len(deliveries) >= 2, "several invoices are numbered in the report year and dated in the year before")
    # freight revenue (4050) is billed on the invoice header and reduced by the freight credits of credit memos, which post to 4050
    # and not to 4060, whose balance is the credit memos' subtotals
    freight_acct, returns_acct = d.account("4050"), d.account("4060")
    freight_billed = d.one("SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'SalesInvoice'",
                           freight_acct, y)
    freight_credits = d.one("SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND SourceDocumentType = 'CreditMemo'",
                            freight_acct, y)
    freight_net = d.one(f"SELECT ROUND(SUM(Credit) - SUM(Debit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}", freight_acct, y)
    memo_freight = d.one("SELECT ROUND(SUM(FreightCreditAmount), 2) FROM CreditMemo WHERE CreditMemoDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")
    memo_subtotal = d.one("SELECT ROUND(SUM(SubTotal), 2) FROM CreditMemo WHERE CreditMemoDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")
    returns_balance = d.one(f"SELECT ROUND(SUM(Debit) - SUM(Credit), 2) FROM GLEntry WHERE AccountID = ? AND FiscalYear = ? AND {d.no_closes()}", returns_acct, y)
    claim(freight_credits > 0 and abs(freight_billed - freight_credits - freight_net) < 0.005,
          "freight revenue (4050) is the freight billed on invoices less freight credits on credit memos")
    claim(abs(memo_freight - freight_credits) < 0.005 and abs(memo_subtotal - returns_balance) < 0.005,
          "the freight credits of the credit memos post to 4050, and 4060 holds the credit memos' subtotals only, so the freight credits are not deducted twice")
    return dict(c1=c1, c2=c2, earlier_close_f=" and ".join(d.closes_of(d.F)), earlier_close_p=" and ".join(d.closes_of(d.P)),
                deliveries=deliveries, freight_billed=freight_billed, freight_credits=freight_credits, freight_net=freight_net,
                rows_all=rows_all, rows_next=rows_next, rows_close=rows_close, kept=kept, cash=cash_bal, cash_all=cash_all,
                cash_gap=round(cash_bal - cash_all, 2), cogs=[dict(number=n, name=nm, balance=b) for n, nm, b in cogs],
                letters={c: col_letter(i + 1) for i, c in enumerate(TB_COLUMNS)}, n_accounts_all=d.one("SELECT COUNT(*) FROM Account"),
                acct=dict(freight=4050, returns=4060, loss=7020, interest=7030), zero_accounts=and_join(zero_accounts))


# --- Exercise 6.2: disaggregating revenue --------------------------------------------------------------------------------

@context("ch06.g2")
def g2(d, claim):
    schema(d, claim, {"Customer": ["CustomerID", "CustomerSegment", "Region"], "Item": ["ItemID", "ItemGroup"]})
    y, p = d.C, d.P
    now, before = lines(d, y), lines(d, p)
    combos: dict = {}
    for r in before:
        combos.setdefault((r["segment"], r["grp"]), [0.0, 0.0])[0] += r["R"]
    for r in now:
        combos.setdefault((r["segment"], r["grp"]), [0.0, 0.0])[1] += r["R"]
    claim(all(v[0] > 0 for v in combos.values() if v[1] > 0),
          "every combination with revenue in the report year also has revenue in the previous year, so % Difference From finds a base everywhere")
    grand = sum(v[1] for v in combos.values())
    big = [k for k, v in combos.items() if v[0] >= 500000]
    seg_share = sorted(((s, sum(v[1] for k, v in combos.items() if k[0] == s) / grand) for s in {k[0] for k in combos}), key=lambda t: -t[1])
    grp_share = {g: sum(v[1] for k, v in combos.items() if k[1] == g) / grand for g in GROUPS}
    claim({k[1] for k in combos if k[0] == "Design Services"} == {"Services"} and {k[0] for k in combos if k[1] == "Services"} == {"Design Services"},
          "Design Services buys only Services, and only Design Services buys Services, so the segment and the product line coincide there")
    # the combinations the $500,000 floor leaves out, and why it matters
    small = sorted(((s, g, v[0], v[1], v[1] / v[0] - 1) for (s, g), v in combos.items() if v[0] < 500000), key=lambda t: -abs(t[4]))
    ranked_big = sorted((v[1] / v[0] - 1 for k, v in combos.items() if k in big))
    claim(abs(small[0][4]) > ranked_big[-1] or abs(small[0][4]) > abs(ranked_big[0]),
          "a combination below the $500,000 floor has a larger percentage change than the largest ranked ones, so the floor matters")
    regions = sorted({r["region"] for r in now})
    claim(len(regions) == 4, "the customers are in four regions")
    svc = []
    for reg in regions:
        a = sum(r["R"] for r in before if r["region"] == reg and r["grp"] == "Services")
        b = sum(r["R"] for r in now if r["region"] == reg and r["grp"] == "Services")
        svc.append((reg, a, b, b / a - 1))
    claim(max(abs(x[3]) for x in svc) > 1.0, "design services revenue by region swings by more than 100 percent in one region, on a small base")
    # the ledger's operating revenue, for the reconciliation of requirement 5
    c1, c2 = d.closes_of(y)
    opr = d.one("SELECT ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountSubType = 'Operating Revenue' "
                "AND g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?)", f"{d.N}-01-01", c1, c2)
    cutoff = d.one("SELECT ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber IN (4010, 4020, 4030, 4040, 4080) "
                   "AND g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?)", f"{d.N}-01-01", c1, c2) - grand
    freight = d.one("SELECT ROUND(SUM(g.Credit) - SUM(g.Debit), 2) FROM GLEntry g JOIN Account a ON a.AccountID = g.AccountID WHERE a.AccountNumber = 4050 "
                    "AND g.PostingDate < ? AND g.VoucherNumber NOT IN (?, ?)", f"{d.N}-01-01", c1, c2)
    claim(abs(grand + cutoff + freight - opr) < 0.01, "the invoice lines plus the cutoff invoices plus freight revenue equal the operating revenue of the income statement")
    return dict(y=y, p=p, n_combos=len(combos), n_big=len(big), grand=grand, prior_total=sum(v[0] for v in combos.values()), seg_share=seg_share,
                grp_share=grp_share, n_segments=len({k[0] for k in combos}), regions=regions, n_regions=len(regions),
                small=[dict(segment=s, group=g, prior=a, now=b, change=ch) for s, g, a, b, ch in small[:2]],
                svc=sorted((dict(region=r, prior=a, now=b, change=ch) for r, a, b, ch in svc), key=lambda x: -abs(x["change"])), opr=opr, cutoff=round(cutoff, 2), freight=freight)


# --- Exercise 6.3: product-line profitability -----------------------------------------------------------------------------

@context("ch06.g3")
def g3(d, claim):
    y = d.C
    rows = lines(d, y)
    groups = {}
    for g in GROUPS:
        rev = sum(r["R"] for r in rows if r["grp"] == g)
        cost = sum(r["C"] for r in rows if r["grp"] == g)
        groups[g] = dict(revenue=rev, margin=rev - cost, pct=(rev - cost) / rev)
    types: dict = {}
    for r in rows:
        if r["grp"] == "Furniture":
            t = types.setdefault(r["type"], [0.0, 0.0])
            t[0] += r["R"]
            t[1] += r["C"]
    claim(sorted(types) == sorted(TYPE_NAMES), "the Furniture lines of the year cover the eight product types of Chapter 5")
    ranked = sorted(((c, TYPE_NAMES[c][0], (v[0] - v[1]) / v[0], v[0] - v[1], v[0]) for c, v in types.items()), key=lambda t: -t[2])
    total_rev = sum(x["revenue"] for x in groups.values())
    total_margin = sum(x["margin"] for x in groups.values())
    gap = ranked[0][2] - ranked[-1][2]
    claim(gap < 0.06, "the Furniture product types differ by less than six points of margin, so the ranking is a matter of a few points")
    claim(all(x["margin"] / total_margin < x["revenue"] / total_rev for x in [groups["Services"]]) is False,
          "the Services margin of 100 percent lifts the grand total, so the grand total's margin percentage overstates the product lines")
    services_staff = d.one("SELECT COUNT(DISTINCT EmployeeID) FROM ServiceTimeEntry WHERE WorkDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31") \
        if [r for r in d.q("PRAGMA table_info(ServiceTimeEntry)") if r[1] == "EmployeeID"] else None
    claim([r for r in d.q("PRAGMA table_info(ServiceTimeEntry)") if r[1] == "ExtendedCost"] and
          [r for r in d.q("PRAGMA table_info(ServiceTimeEntry)") if r[1] == "WorkDate"], "ServiceTimeEntry has ExtendedCost and WorkDate")
    schema(d, claim, {"ServiceTimeEntry": ["WorkDate", "BillableHours", "NonBillableHours", "CostRateUsed", "ExtendedCost"]})
    # the time-entry cost covers every hour recorded on a work date of the year, nonbillable hours included, so it is not
    # the cost of the hours billed; neither it nor the salaries account is a matched service margin
    time_all, time_billable, hours_nonbillable = d.q("SELECT ROUND(SUM(ExtendedCost), 2), ROUND(SUM(BillableHours * CostRateUsed), 2), ROUND(SUM(NonBillableHours), 2) "
                                                     "FROM ServiceTimeEntry WHERE WorkDate BETWEEN ? AND ?", f"{y}-01-01", f"{y}-12-31")[0]
    claim(hours_nonbillable > 0 and time_all > time_billable,
          "the time-entry cost of the year includes nonbillable hours, so it exceeds the cost of the billable hours alone")
    # shares with Services left in the denominators, and the TBL code shared with another group
    with_services = {g: (x["revenue"] / total_rev, x["margin"] / total_margin) for g, x in groups.items()}
    flips = [g for g in PRODUCTS if (groups[g]["margin"] / (total_margin - groups["Services"]["margin"]) > groups[g]["revenue"] / (total_rev - groups["Services"]["revenue"]))
             != (with_services[g][1] > with_services[g][0])]
    claim(flips == ["Lighting"], "leaving Services in the denominators reverses the comparison for Lighting only: its margin share falls below its revenue share")
    tbl = [r for r in rows if r["type"] == "TBL"]
    tbl_all = 1 - sum(r["C"] for r in tbl) / sum(r["R"] for r in tbl)
    tbl_furniture = dict((c, p) for c, _, p, _, _ in ranked)["TBL"]
    claim(any(r["grp"] != "Furniture" for r in tbl) and abs(tbl_all - tbl_furniture) > 0.005,
          "the product type code TBL is also used outside Furniture, and its margin differs by more than half a point when the Furniture filter is missing")
    # adjacent types whose margin percentages display alike at two decimals although the unrounded values differ
    ties = [dict(a=a[0], b=b[0], shown=round(100 * a[2], 2), a_pct=a[2], b_pct=b[2]) for a, b in zip(ranked, ranked[1:])
            if round(100 * a[2], 2) == round(100 * b[2], 2) and a[2] != b[2]]
    claim(len(ties) == 1, "exactly two adjacent Furniture product types display the same margin percentage at two decimals although their unrounded margins differ, so a sort on the displayed values can tie")
    pos = {r[0]: i for i, r in enumerate(ranked)}
    claim(all(2 <= pos[t["a"]] <= len(ranked) - 3 and 2 <= pos[t["b"]] <= len(ranked) - 3 for t in ties),
          "the tied types are neither among the two highest nor among the two lowest, so the answer to requirement (3) does not depend on the tie")
    return dict(groups=groups, grand_revenue=total_rev, grand_margin=total_margin, grand_pct=total_margin / total_rev, types=ranked, ties=ties,
                time_all=time_all, time_billable=time_billable, hours_nonbillable=hours_nonbillable,
                product_revenue=total_rev - groups["Services"]["revenue"], product_margin=total_margin - groups["Services"]["margin"],
                type_gap_pts=100 * gap, with_services=with_services, flips=and_join(flips), tbl_all=tbl_all, tbl_furniture=tbl_furniture)


# --- Exercise 6.4: the margin bridge by product type -----------------------------------------------------------------------

@context("ch06.g4")
def g4(d, claim):
    fb = furniture_bridge(d)
    rows = [r for r in lines(d, d.C) if r["grp"] == "Furniture" and r["q"] in (3, 4)]
    agg: dict = {}
    for r in rows:
        a = agg.setdefault((r["type"], r["q"]), dict(U=0.0, R=0.0, C=0.0, D=0.0))
        a["U"] += r["U"]
        a["R"] += r["R"]
        a["C"] += r["C"]
        a["D"] += r["D"]
    codes = sorted({t for t, _ in agg})
    u3 = sum(agg[(t, 3)]["U"] for t in codes)
    out = []
    for t in codes:
        a, b = agg[(t, 3)], agg[(t, 4)]
        out.append(dict(code=t, name=TYPE_NAMES[t][0], u3=a["U"], u4=b["U"], p3=a["R"] / a["U"], p4=b["R"] / b["U"], c3=a["C"] / a["U"],
                        c4=b["C"] / b["U"], share3=a["U"] / u3, m3=(a["R"] - a["C"]) / a["U"]))
    promo_type = -sum(agg[(t, 4)]["U"] * (agg[(t, 4)]["D"] / agg[(t, 4)]["U"] - agg[(t, 3)]["D"] / agg[(t, 3)]["U"]) for t in codes)
    claim(abs(sum(x["u3"] for x in out) - fb["q3"]["U"]) < 1e-6 and abs(sum(x["u4"] for x in out) - fb["q4"]["U"]) < 1e-6,
          "the eight product types add up to the Furniture units of Tutorial 6.3")
    e = fb["effects"]
    top = max(out, key=lambda x: abs(x["c4"] - x["c3"]))
    same = [x["code"] for x in out if x is not top and x["p4"] < x["p3"] and x["c4"] < x["c3"]]
    claim(len(same) > 0, "another product type besides the one with the largest change in cost per unit has price and cost per unit that both fall")
    # the four effects of the product-type bridge, to explain the quantity effect a student may sum by type and the cent of rounding
    u4 = sum(x["u4"] for x in out)
    price = sum(x["u4"] * (x["p4"] - x["p3"]) for x in out)
    cost = -sum(x["u4"] * (x["c4"] - x["c3"]) for x in out)
    volume = (u4 - u3) * fb["q3"]["M"] / u3
    mix = sum((x["u4"] - u4 * x["share3"]) * x["m3"] for x in out)
    combined = sum((x["u4"] - x["u3"]) * x["m3"] for x in out)
    claim(abs(combined - (volume + mix)) < 1e-6,
          "each type's unit change times its third-quarter margin per unit, summed over the types, is the volume effect plus the mix effect, so adding the mix effect to it counts the mix twice")
    claim(abs(price + cost + volume + mix - fb["change"]) < 1e-6, "the four effects of the product-type bridge add up to the change in margin")
    rounded_sum = round(sum(round(v, 2) for v in (price, cost, volume, mix)), 2)
    rounded_change = round(fb["change"], 2)
    claim(abs(rounded_sum - rounded_change) > 0.005 and abs(rounded_sum - rounded_change) < 0.015,
          "the four effects rounded separately to cents sum to a cent away from the rounded change in margin")
    return dict(same_types=and_join(same), types=out, n_types=len(out), q3=fb["q3"]["M"], q4=fb["q4"]["M"], change=fb["change"], t_volume=e["volume"], t_mix=e["mix"],
                combined=combined, rounded_sum=rounded_sum, rounded_change=rounded_change,
                t_price=e["price_lists"] + e["promotions"], t_lists=e["price_lists"], t_promo=e["promotions"], promo_type=promo_type,
                u3=u3, u4=fb["q4"]["U"], m3=fb["q3"]["m"], r3=fb["q3"]["R"], r4=fb["q4"]["R"], k3=fb["q3"]["C"], k4=fb["q4"]["C"])


# --- Exercise 6.5: a substantive analytical procedure ----------------------------------------------------------------------

@context("ch06.g5")
def g5(d, claim):
    now, before = lines(d, d.C), lines(d, d.P)
    rows = []
    for g in GROUPS:
        for q in range(1, 5):
            exp, act = total(before, "R", grp=g, q=q), total(now, "R", grp=g, q=q)
            rows.append(dict(group=g, q=q, exp=exp, act=act, diff=act - exp, pct=(act - exp) / exp))
    thr_pct, thr_usd = 0.10, 50000
    both = [r for r in rows if abs(r["diff"]) > thr_pct * r["exp"] and abs(r["diff"]) > thr_usd]
    only_usd = [r for r in rows if abs(r["diff"]) > thr_usd]
    only_pct = [r for r in rows if abs(r["diff"]) > thr_pct * r["exp"]]
    claim(len(only_usd) > len(both) and len(only_pct) == len(both),
          "every difference over 10 percent of its expectation also exceeds $50,000, so the percentage condition decides what is flagged and a dollar threshold alone would flag more")
    flagged_set = {(r["group"], r["q"]) for r in both}
    extra_usd = [r for r in only_usd if (r["group"], r["q"]) not in flagged_set]
    claim(any(r["group"] == "Furniture" for r in extra_usd), "a dollar threshold alone would flag Furniture differences that the two thresholds miss")
    services = [r for r in both if r["group"] == "Services"]
    claim(len(services) >= 1, "Services has flagged differences")
    pick = services[-1]
    growth = sum(r["R"] for r in now) / sum(r["R"] for r in before) - 1
    claim(0 < growth < 0.02, "total revenue grew by about one percent, so prior-year revenue is a close but imperfect expectation")
    n_dec = sum(1 for r in both if r["diff"] < 0)
    claim(0 < n_dec < len(both), "the flagged differences include both increases and decreases, so a test that flags only increases misses some")
    union = {(r["group"], r["q"]) for r in only_usd} | {(r["group"], r["q"]) for r in only_pct}
    claim(len(union) == len(only_usd), "the differences that exceed $50,000 include every difference over 10 percent, so a dollar threshold alone and an either-or rule flag the same number")
    adjusted = [r for r in rows if abs(r["act"] - r["exp"] * (1 + growth)) > thr_pct * r["exp"] * (1 + growth) and abs(r["act"] - r["exp"] * (1 + growth)) > thr_usd]
    furniture_q4 = next(r for r in rows if r["group"] == "Furniture" and r["q"] == 4)
    claim(abs(furniture_q4["diff"]) == max(abs(r["diff"]) for r in rows) and (furniture_q4["group"], furniture_q4["q"]) not in flagged_set,
          "the largest difference in dollars is Furniture's fourth quarter, and the two thresholds do not flag it")
    rank = {r["group"]: i for i, r in enumerate(sorted([dict(group=g, rev=total(now, "R", grp=g)) for g in GROUPS], key=lambda r: -r["rev"]))}
    return dict(rows=rows, both=both, only_usd=len(only_usd), only_pct=len(only_pct), extra_usd=[dict(r) for r in extra_usd], pick=pick, growth=growth,
                n_cells=len(rows), n_groups=len(GROUPS), furniture_rank=rank["Furniture"] + 1, n_dec=n_dec, n_inc=len(both) - n_dec, n_or=len(union),
                n_adjusted=len(adjusted), furniture_q4=furniture_q4)


# --- Exercise 6.6: a descriptive profile of the revenue population ---------------------------------------------------------

@context("ch06.g6")
def g6(d, claim):
    schema(d, claim, {"Customer": ["CustomerID", "CustomerName", "CustomerSegment"], "PromotionProgram": ["PromotionID", "PromotionName", "EffectiveStartDate", "EffectiveEndDate"]})
    y = d.C
    rows = lines(d, y)
    revenue = sum(r["R"] for r in rows)
    names: dict = {}
    for r in rows:
        names.setdefault(r["name"], set()).add(r["customer"])
    same = sorted((n, sorted(ids)) for n, ids in names.items() if len(ids) > 1)
    claim(len(same) >= 1, "two customers invoiced in the year share a name, so a PivotTable by CustomerName would merge them")
    # the ranking by name instead of by CustomerID: the two customers named alike merge, and one enters the top ten
    by_key: dict = {}
    by_name: dict = {}
    for r in rows:
        by_key[r["customer"]] = by_key.get(r["customer"], 0.0) + r["R"]
        by_name[r["name"]] = by_name.get(r["name"], 0.0) + r["R"]
    top10_key = sum(sorted(by_key.values(), reverse=True)[:10]) / revenue
    top10_name = sum(sorted(by_name.values(), reverse=True)[:10]) / revenue
    merged = same[0][0] if same else ""
    rank_name = sorted(by_name, key=lambda n: -by_name[n]).index(merged) + 1 if merged else 0
    claim(merged and 1 <= rank_name <= 10 and abs(top10_name - top10_key) > 0.001,
          "the two customers that share a name together rank among the ten largest when grouped by name, which changes the share of the ten largest")
    promo_lines = [r for r in rows if r["promo"] is not None]
    claim(len(promo_lines) < 0.1 * len(rows), "promotion lines are under a tenth of the year's lines")
    info = {k: v for k, v in ((r[0], r[1:]) for r in d.q("SELECT PromotionID, PromotionName, EffectiveStartDate, EffectiveEndDate FROM PromotionProgram"))}
    pids = sorted({r["promo"] for r in promo_lines})
    late = [k for k in pids if info[k][1][:4] == str(d.P)]
    # a promotion whose end date is before its start date
    backwards = [k for k in pids if info[k][2] < info[k][1]]
    claim(len(backwards) == 1, "one promotion with lines in the year ends before it starts")
    shares = sorted(((g, sum(1 for r in promo_lines if r["grp"] == g) / sum(1 for r in rows if r["grp"] == g)) for g in GROUPS), key=lambda t: -t[1])
    claim(shares[0][0] == "Furniture" and shares[0][1] > 5 * shares[1][1], "promotions reach about a fifth of the Furniture lines and very few lines of the other groups")
    per_promo: dict = {}
    for r in promo_lines:
        x = per_promo.setdefault(r["promo"], [0, 0.0])
        x[0] += 1
        x[1] += r["D"]
    main_id = max(per_promo, key=lambda k: per_promo[k][0])
    claim(main_id == max(per_promo, key=lambda k: per_promo[k][1]), "the promotion with the most lines also has the most discount")
    # the controls of Steps 4 and 6: the lines of each group, and those that carry a promotion
    group_counts = [dict(group=g, promo=sum(1 for r in promo_lines if r["grp"] == g), lines=sum(1 for r in rows if r["grp"] == g)) for g in GROUPS]
    claim(sum(x["promo"] for x in group_counts) == len(promo_lines) and sum(x["lines"] for x in group_counts) == len(rows),
          "the groups' lines and promotion lines add up to the year's lines and promotion lines")
    return dict(main_id=main_id, group_counts=group_counts, main_lines=per_promo[main_id][0], main_discount=per_promo[main_id][1], top10_key=top10_key, top10_name=top10_name, merged=merged, rank_name=rank_name, merged_total=by_name.get(merged, 0.0),
                revenue=revenue, n_lines=len(rows), n_promo=len(promo_lines), promo_discount=sum(r["D"] for r in promo_lines), n_blank=len(rows) - len(promo_lines),
                same=[dict(name=n, ids=and_join(ids)) for n, ids in same], names=info, late=late, late_names=and_join(info[k][0] for k in late),
                backwards=backwards[0], backwards_start=info[backwards[0]][1], backwards_end=info[backwards[0]][2], n_customers=len({r["customer"] for r in rows}))
