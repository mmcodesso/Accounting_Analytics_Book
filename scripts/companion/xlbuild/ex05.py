"""Chapter 5 Exercises - Solutions.xlsx: the solutions to the exercises of Chapter 5.

The workbook starts from the verified end-of-Chapter-5 companion file (Charles River Furniture Analysis.xlsx at the end
of Tutorial 5.3), the "fresh copy of your analysis workbook" the exercises ask for. Each exercise adds its worksheets
before the Solution Notes tab: one named after the exercise (Ex 5.1, ...) with its grids, lists, and model answers, and
one for each Table it loads with Power Query (Ex 5.1 CreditMemo, ...). The tutorials' queries are never edited; the
exercises add calculated columns to the tutorial Tables where a requirement says so (SalesInvoice in Exercises 5.2
and 5.4, SalesInvoiceLine in Exercise 5.6).

Every check compares a live formula with a value computed here from CharlesRiver.sqlite (read-only), independently of
Excel, and those values are the ones the instructor notes state (facts/notes/ch05.py).

What the builder decides where the text leaves a choice (cell notes in the workbook say so where a reader would look):
  - Exercise 5.5 asks for a new workbook. The solution keeps one workbook for all six exercises, so its Supplier,
    Employee, and DisbursementPayment Tables are worksheets of this file (Exercise 5.6 says "the workbook of
    Exercise 5.5", and it is this one).
  - Exercise 5.5's Supplier query keeps the identifying columns (SupplierID, SupplierName, TaxID, BankAccount) and the
    address columns, and also IsApproved and SupplierRiskRating, which Exercise 5.6 uses on the same Table. Its
    Employee query also keeps JobTitle, which requirement (3) brings onto the Supplier Table.
  - Exercise 5.1 uses lookups (XLOOKUP with "No match", as in Tutorial 5.2), not merges, and assigns the credits to
    the quarter of the CreditMemoDate. Requirement (4)'s comparison adds two rows: the Furniture credits of the year
    for invoices of earlier years, and the net revenue with those credits moved to the original invoice's year.
  - Exercise 5.2 compares its flags with Tutorial 2.1's invoices dated before their first shipment. That list comes
    from the Part I workbook, which this file does not include (it never loads the Shipment Table), so it is typed
    as values, taken from the dataset when the file was built.
  - Exercise 5.6's duplicate test counts equal values with SUM(--(range=value)) rather than COUNTIF: the masked
    BankAccount values begin with asterisks, which COUNTIF reads as wildcards.
  - Written answers (explanations and memos) are model answers, labeled "Model answer", consistent with the
    instructor notes.
"""

from __future__ import annotations

import math
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date
from functools import cached_property
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import DB, db_uri  # noqa: E402
from xlbuild import xl  # noqa: E402
from xlbuild.analysis import formulas, nav, values  # noqa: E402
from xlbuild.expected import percentile_inc  # noqa: E402
from xlbuild.solutions import COUNT, MONEY, PCT, RATIO, ExerciseBuild, exercise_info  # noqa: E402

CHAPTER = 5
DATE = "yyyy-mm-dd"
# CharlesRiver.xlsx Table numbers (T<n>_<Table>), in the workbook's worksheet order
TABLES = {"CreditMemo": 23, "CreditMemoLine": 24, "Supplier": 31, "PurchaseOrder": 33, "DisbursementPayment": 39,
          "Item": 44, "Employee": 74}
# Tutorial 5.1's Furniture product types (tbl-05-03), the row labels Exercise 5.3 asks for
PRODUCT_TYPES = [("BKC", "Bookcase"), ("BNH", "Bench"), ("CON", "Console table"), ("CTB", "Coffee table"),
                 ("DSK", "Desk"), ("NGT", "Nightstand"), ("SDB", "Sideboard"), ("TBL", "Dining table")]
PLURAL = dict(BKC="bookcases", BNH="benches", CON="consoles", CTB="coffee tables", DSK="desks", NGT="nightstands",
              SDB="sideboards", TBL="dining tables")
SHARE_THRESHOLD = 0.02                      # Exercise 5.3 (3): more than two percentage points
SUPPLIER_COLUMNS = ["SupplierID", "SupplierName", "Address", "City", "State", "PostalCode", "Country", "IsApproved",
                    "TaxID", "BankAccount", "SupplierRiskRating"]      # in the Table's order (Choose Columns keeps it)
EMPLOYEE_COLUMNS = ["EmployeeID", "EmployeeName", "JobTitle", "Address", "City", "State"]


# --- small helpers ---------------------------------------------------------------------------------------------------

def quarter(iso: str) -> str:
    return f"{iso[:4]}-Q{(int(iso[5:7]) + 2) // 3}"


def serial(iso: str) -> int:
    """An ISO date as Excel's date serial number."""
    return (date.fromisoformat(iso[:10]) - date(1899, 12, 30)).days


def long_date(iso: str, year: bool = True) -> str:
    import calendar
    d = date.fromisoformat(iso[:10])
    return f"{calendar.month_name[d.month]} {d.day}" + (f", {d.year}" if year else "")


def excel_trim(text: str) -> str:
    """Excel's TRIM: no leading or trailing spaces, and runs of spaces inside reduced to one."""
    return re.sub(" +", " ", text.strip(" "))


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


def series(items) -> str:
    items = [str(i) for i in items]
    return " and ".join(items) if len(items) <= 2 else ", ".join(items[:-1]) + ", and " + items[-1]


WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else f"{n:,}"


def new_sheet(b: ExerciseBuild, name: str):
    return xl.sheet(b.wb, name, before=b.wb.Worksheets("Solution Notes"))


def heading(ws, e: str) -> None:
    info = exercise_info(CHAPTER, int(e.split(".")[1]))
    ws.Range("A1").Value = f"Exercise {e}: {info['title']}"
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 13


def header_row(ws, row: int, labels: list[str], col: int = 1) -> None:
    for j, label in enumerate(labels):
        ws.Cells(row, col + j).Value = label
    ws.Range(ws.Cells(row, col), ws.Cells(row, col + len(labels) - 1)).Font.Bold = True


def text_cell(ws, addr: str, text: str) -> None:
    """A label such as 2026-Q3, kept as text."""
    ws.Range(addr).NumberFormat = "@"
    ws.Range(addr).Value = text


def section(ws, addr: str, text: str) -> None:
    ws.Range(addr).Value = text
    ws.Range(addr).Font.Bold = True


def model_answer(ws, row: int, label: str, text: str, last: str = "I") -> int:
    """A labeled model answer: the label in column A, the text below it in a wrapped cell merged across A:last.
    Returns the next free row."""
    ws.Cells(row, 1).Value = label
    ws.Cells(row, 1).Font.Bold = True
    rng = ws.Range(f"A{row + 1}:{last}{row + 1}")
    rng.Merge()
    rng.WrapText = True
    rng.VerticalAlignment = -4160                      # top
    rng.Cells(1, 1).Value = text
    width = sum(ws.Columns(c).ColumnWidth for c in range(1, ws.Range(f"{last}1").Column + 1))
    lines = sum(max(1, math.ceil(len(p) * 1.08 / width)) for p in text.split("\n"))
    ws.Rows(row + 1).RowHeight = min(409, 15 * lines + 6)
    return row + 3


def note(ws, addr: str, text: str) -> None:
    ws.Range(addr).AddComment(text)


def load(b: ExerciseBuild, query: str, table: str, sheet_name: str, after, corrections=None, extra=()):
    xl.add_query(b.wb, query, nav(b, TABLES[table], table, corrections, extra))
    return xl.load_query(b.wb, query, sheet_name, after=after)


def select_in_order(columns: list[str]) -> str:
    return "Table.SelectColumns({prev},{" + ", ".join(f'"{c}"' for c in columns) + "})"


# --- expected values, from CharlesRiver.sqlite (read-only) ------------------------------------------------------------

class Facts:
    def __init__(self, year: int):
        self.year = year
        con = sqlite3.connect(db_uri(), uri=True)
        try:
            q = lambda sql, *a: con.execute(sql, a).fetchall()
            self.items = {r[0]: dict(code=r[1], name=r[2], group=r[3], list=r[4], status=r[5], active=r[6], launch=r[7])
                          for r in q("SELECT ItemID, ItemCode, ItemName, ItemGroup, ListPrice, LifecycleStatus, IsActive, "
                                     "LaunchDate FROM Item")}
            self.invoices = {r[0]: dict(number=r[1], date=r[2][:10], order=r[3], subtotal=r[4])
                             for r in q("SELECT SalesInvoiceID, InvoiceNumber, InvoiceDate, SalesOrderID, SubTotal "
                                        "FROM SalesInvoice")}
            self.orders = {r[0]: dict(number=r[1], date=r[2][:10])
                           for r in q("SELECT SalesOrderID, OrderNumber, OrderDate FROM SalesOrder")}
            self.lines = [dict(inv=r[0], item=r[1], qty=r[2], lt=r[3], promo=r[4])
                          for r in q("SELECT SalesInvoiceID, ItemID, Quantity, LineTotal, PromotionID "
                                     "FROM SalesInvoiceLine")]
            self.memos = {r[0]: dict(number=r[1], date=r[2][:10], invoice=r[3], subtotal=r[4])
                          for r in q("SELECT CreditMemoID, CreditMemoNumber, CreditMemoDate, OriginalSalesInvoiceID, "
                                     "SubTotal FROM CreditMemo")}
            self.memo_lines = [dict(memo=r[0], item=r[1], lt=r[2])
                               for r in q("SELECT CreditMemoID, ItemID, LineTotal FROM CreditMemoLine")]
            self.first_shipment = {r[0]: r[1][:10] for r in q("SELECT SalesOrderID, MIN(ShipmentDate) FROM Shipment "
                                                               "GROUP BY SalesOrderID")}
            self.promotions = [dict(id=r[0], code=r[1], start=r[2][:10], end=r[3][:10])
                               for r in q("SELECT PromotionID, PromotionCode, EffectiveStartDate, EffectiveEndDate "
                                          "FROM PromotionProgram ORDER BY PromotionID")]
            self.suppliers = [dict(id=r[0], name=r[1], address=r[2], city=r[3], tax=r[4], bank=r[5], approved=r[6],
                                   risk=r[7])
                              for r in q("SELECT SupplierID, SupplierName, Address, City, TaxID, BankAccount, IsApproved, "
                                         "SupplierRiskRating FROM Supplier ORDER BY SupplierID")]
            self.employees = [dict(id=r[0], name=r[1], title=r[2], address=r[3], city=r[4])
                              for r in q("SELECT EmployeeID, EmployeeName, JobTitle, Address, City FROM Employee "
                                         "ORDER BY EmployeeID")]
            self.payments = {r[0]: (r[1], r[2]) for r in q("SELECT SupplierID, COUNT(*), SUM(Amount) "
                                                             "FROM DisbursementPayment GROUP BY SupplierID")}
            self.purchase_orders = dict(q("SELECT SupplierID, COUNT(*) FROM PurchaseOrder GROUP BY SupplierID"))
        finally:
            con.close()

    def periods(self) -> list[str]:
        return [f"{self.year}-Q{k}" for k in range(1, 5)]

    def furniture_by_quarter(self) -> dict[str, float]:
        out = {p: 0.0 for p in self.periods()}
        for l in self.lines:
            p = quarter(self.invoices[l["inv"]]["date"])
            if p in out and self.items[l["item"]]["group"] == "Furniture":
                out[p] += l["lt"]
        return out

    # --- Exercise 5.1 ----------------------------------------------------------------------------------------------
    @cached_property
    def ex1(self) -> dict:
        y = str(self.year)
        listed = {i for i, it in self.items.items() if it["list"] is not None}     # the tutorial's Item Table
        credits = {p: [0, 0.0] for p in self.periods()}
        earlier_furniture = {p: 0.0 for p in self.periods()}
        unmatched = 0
        earlier = {m for m, v in self.memos.items()
                   if v["date"][:4] == y and v["invoice"] in self.invoices and self.invoices[v["invoice"]]["date"][:4] < y}
        earlier_lines = 0
        for cl in self.memo_lines:
            memo = self.memos.get(cl["memo"])
            unmatched += (memo is None) + (cl["item"] not in listed)
            if memo is None or cl["item"] not in listed:
                continue
            earlier_lines += cl["memo"] in earlier
            p = quarter(memo["date"])
            if p in credits and self.items[cl["item"]]["group"] == "Furniture":
                credits[p][0] += 1
                credits[p][1] += cl["lt"]
                if cl["memo"] in earlier:
                    earlier_furniture[p] += cl["lt"]
        gross = self.furniture_by_quarter()
        memo_list = sorted((self.memos[m]["number"], self.memos[m]["date"], self.invoices[self.memos[m]["invoice"]]["number"],
                            self.invoices[self.memos[m]["invoice"]]["date"]) for m in earlier)
        return dict(gross=gross, credits=credits, net={p: gross[p] - credits[p][1] for p in gross}, unmatched=unmatched,
                    earlier_memos=len(earlier), earlier_lines=earlier_lines, earlier_furniture=earlier_furniture,
                    earlier_list=memo_list,
                    earlier_furniture_lines=sum(1 for cl in self.memo_lines if cl["memo"] in earlier
                                                and self.items[cl["item"]]["group"] == "Furniture"))

    # --- Exercise 5.2 ----------------------------------------------------------------------------------------------
    @cached_property
    def ex2(self) -> dict:
        prefix = sorted(v["number"] for v in self.invoices.values() if int(v["number"][3:7]) != int(v["date"][:4]))
        before_order = sorted(v["number"] for v in self.invoices.values()
                              if v["order"] in self.orders and v["date"] < self.orders[v["order"]]["date"])
        flagged = sorted(set(prefix) | set(before_order))
        tutorial21 = sorted((v["number"], v["date"], self.first_shipment[v["order"]]) for v in self.invoices.values()
                            if v["order"] in self.first_shipment and v["date"] < self.first_shipment[v["order"]])
        no_order = sum(1 for v in self.invoices.values() if v["order"] not in self.orders)
        order_mismatch = sum(1 for o in self.orders.values() if int(o["number"][3:7]) != int(o["date"][:4]))
        by_number = {v["number"]: v for v in self.invoices.values()}
        return dict(prefix=prefix, before_order=before_order, flagged=flagged, tutorial21=tutorial21,
                    no_order=no_order, order_mismatch=order_mismatch,
                    in_t21=sum(1 for n in flagged if n in {t[0] for t in tutorial21}),
                    t21_missed=sum(1 for t in tutorial21 if t[0] not in flagged),
                    prefix_rows=[by_number[n] for n in prefix], order_rows=[by_number[n] for n in before_order],
                    invoices=len(self.invoices))

    # --- Exercise 5.3 ----------------------------------------------------------------------------------------------
    @cached_property
    def ex3(self) -> dict:
        q3, q4 = f"{self.year}-Q3", f"{self.year}-Q4"
        grid = defaultdict(lambda: {q3: [0.0, 0.0], q4: [0.0, 0.0]})
        lines = fractional = 0
        for l in self.lines:
            p = quarter(self.invoices[l["inv"]]["date"])
            it = self.items[l["item"]]
            if p in (q3, q4) and it["group"] == "Furniture":
                g = grid[it["code"][4:7]][p]
                g[0] += l["lt"]
                g[1] += l["qty"]
                lines += 1
                fractional += not float(l["qty"]).is_integer()
        assert sorted(grid) == [c for c, _ in PRODUCT_TYPES], f"Furniture product types {sorted(grid)}"
        t3, t4 = sum(g[q3][0] for g in grid.values()), sum(g[q4][0] for g in grid.values())
        share = {c: (grid[c][q3][0] / t3, grid[c][q4][0] / t4) for c in grid}
        change = {c: s4 - s3 for c, (s3, s4) in share.items()}
        return dict(q3=q3, q4=q4, grid=dict(grid), t3=t3, t4=t4, share=share, change=change,
                    highlighted=sum(1 for c in change if abs(change[c]) > SHARE_THRESHOLD), lines=lines,
                    fractional=fractional)

    # --- Exercise 5.4 ----------------------------------------------------------------------------------------------
    @cached_property
    def ex4(self) -> dict:
        import statistics
        lags = [((date.fromisoformat(v["date"]) - date.fromisoformat(self.orders[v["order"]]["date"])).days, v["date"])
                for v in self.invoices.values()]
        all_lags = [x for x, _ in lags]
        quarters = {}
        for p in self.periods():
            v = [x for x, d in lags if quarter(d) == p]
            quarters[p] = dict(count=len(v), mean=statistics.mean(v), median=statistics.median(v))
        promos = []
        for p in self.promotions:
            mine = [l for l in self.lines if l["promo"] == p["id"]]
            after = sum(1 for l in mine if self.invoices[l["inv"]]["date"] > p["end"])
            promos.append(dict(p, lines=len(mine), after=after))
        return dict(count=len(all_lags), mean=statistics.mean(all_lags), median=statistics.median(all_lags),
                    p90=percentile_inc(all_lags, 0.9), negative=sum(1 for x in all_lags if x < 0), quarters=quarters,
                    promotions=promos)

    # --- Exercise 5.5 ----------------------------------------------------------------------------------------------
    @cached_property
    def ex5(self) -> dict:
        key = lambda r: (excel_trim(r["address"]) + ", " + excel_trim(r["city"])).upper()
        raw = lambda r: (r["address"].lower(), r["city"].lower())     # COUNTIFS: case-insensitive, no trimming
        emp_keys = defaultdict(list)
        for e in self.employees:
            emp_keys[key(e)].append(e)
        raw_keys = {raw(e) for e in self.employees}
        matches = []
        for s in self.suppliers:
            found = emp_keys.get(key(s), [])
            if found:
                n, total = self.payments.get(s["id"], (0, 0.0))
                matches.append(dict(id=s["id"], name=s["name"], employees=len(found), emp=found[0]["id"],
                                    emp_name=found[0]["name"], title=found[0]["title"], payments=n, paid=total))
        return dict(matches=matches, raw=sum(1 for s in self.suppliers if raw(s) in raw_keys),
                    address_only=sum(1 for s in self.suppliers
                                     if any(excel_trim(e["address"]).upper() == excel_trim(s["address"]).upper()
                                            for e in self.employees)))

    # --- Exercise 5.6 ----------------------------------------------------------------------------------------------
    @cached_property
    def ex6(self) -> dict:
        changed = [(s["name"], proper(s["name"])) for s in self.suppliers if proper(s["name"]) != s["name"]]
        words = defaultdict(int)
        for n, p in changed:
            for a, b in zip(re.findall(r"[^\W\d_]+", n), re.findall(r"[^\W\d_]+", p)):
                if a != b:
                    words[a] += 1
        tax = [s["tax"].lower() for s in self.suppliers]
        bank = [s["bank"].lower() for s in self.suppliers]
        business = lambda s: (self.purchase_orders.get(s, 0), self.payments.get(s, (0, 0.0))[0])
        unapproved = [s for s in self.suppliers if s["approved"] == 0]
        high = [s for s in self.suppliers if s["risk"] == "High"]
        conflict = [(i, it["code"]) for i, it in sorted(self.items.items())
                    if it["status"] == "Discontinued" and it["active"] == 1]
        by_item = defaultdict(list)
        for l in self.lines:
            by_item[l["item"]].append(l)
        inactive = [dict(id=i, code=it["code"], status=it["status"], lines=len(by_item[i]),
                         latest=max(self.invoices[l["inv"]]["date"] for l in by_item[i]))
                    for i, it in sorted(self.items.items()) if it["active"] == 0 and by_item[i]]
        prelaunch = []
        for i, it in sorted(self.items.items()):
            early = [l for l in by_item[i] if self.invoices[l["inv"]]["date"] < it["launch"][:10]]
            if early:
                dates = [self.invoices[l["inv"]]["date"] for l in early]
                prelaunch.append(dict(id=i, code=it["code"], launch=it["launch"][:10], lines=len(early), first=min(dates),
                                      last=max(dates), amount=sum(l["lt"] for l in early)))
        logged = anomaly_keys("prelaunch_item_in_new_activity")
        extra = [i for i in (logged or []) if i not in {p["id"] for p in prelaunch}]
        return dict(suppliers=len(self.suppliers), changed=changed, words=dict(words),
                    tax_shared=sum(1 for t in tax if tax.count(t) > 1),
                    bank_shared=sum(1 for t in bank if bank.count(t) > 1),
                    unapproved=[dict(s, po=business(s["id"])[0], pay=business(s["id"])[1]) for s in unapproved],
                    high=[dict(s, po=business(s["id"])[0], pay=business(s["id"])[1]) for s in high],
                    conflict=conflict, inactive=inactive, prelaunch=prelaunch, extra=extra,
                    extra_lines={i: sum(1 for l in by_item[i]
                                        if self.invoices[l["inv"]]["date"] < self.items[i]["launch"][:10]) for i in extra})


def anomaly_keys(kind: str) -> list[int] | None:
    """The primary keys the generator's AnomalyLog lists for one anomaly type (read-only), or None without the log."""
    path = DB.parent / "CharlesRiver_support.xlsx"
    if not path.is_file():
        return None
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        rows = list(wb["AnomalyLog"].iter_rows(values_only=True))
    finally:
        wb.close()
    t, k = rows[0].index("anomaly_type"), rows[0].index("primary_key_value")
    return sorted(int(r[k]) for r in rows[1:] if r and r[t] == kind)


def facts(b: ExerciseBuild) -> Facts:
    if "facts" not in b.found:
        b.found["facts"] = Facts(b.year)
    return b.found["facts"]


# --- Exercise 5.1 ------------------------------------------------------------------------------------------------------

def ex5_1(b: ExerciseBuild) -> None:
    wb, f, y, e = b.wb, facts(b).ex1, b.year, "5.1"
    ws = new_sheet(b, "Ex 5.1")
    heading(ws, e)
    values(ws, {"A2": "Fiscal year", "B2": y})
    ws.Range("B2").Font.Color = xl.BLUE
    yref = "'Ex 5.1'!$B$2"

    # (1) the credit memos and their lines, with CreditMemoDate set to the Date type (Replace current)
    load(b, "CreditMemo", "CreditMemo", "Ex 5.1 CreditMemo", ws, {"CreditMemoDate": "type date"})
    load(b, "CreditMemoLine", "CreditMemoLine", "Ex 5.1 CreditMemoLine", wb.Worksheets("Ex 5.1 CreditMemo"))
    cm, cml = xl.table(wb, "CreditMemo"), xl.table(wb, "CreditMemoLine")
    cm.ListColumns("CreditMemoDate").DataBodyRange.NumberFormat = DATE
    # (4) the original invoice of each credit memo, and whether it was issued in an earlier year
    xl.add_column(cm, "OriginalInvoiceNumber",
                  '=XLOOKUP([@OriginalSalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[InvoiceNumber],"No match")')
    xl.add_column(cm, "OriginalInvoiceDate",
                  '=XLOOKUP([@OriginalSalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[InvoiceDate],"No match")',
                  DATE)
    xl.add_column(cm, "EarlierYearInvoice",
                  f"=AND(YEAR([@CreditMemoDate])={yref},YEAR([@OriginalInvoiceDate])<{yref})")
    # (2) the lines' date, period, and item group, by lookup
    xl.add_column(cml, "CreditMemoDate",
                  '=XLOOKUP([@CreditMemoID],CreditMemo[CreditMemoID],CreditMemo[CreditMemoDate],"No match")', DATE)
    xl.add_column(cml, "Period", '=YEAR([@CreditMemoDate])&"-Q"&ROUNDUP(MONTH([@CreditMemoDate])/3,0)')
    xl.add_column(cml, "ItemGroup", '=XLOOKUP([@ItemID],Item[ItemID],Item[ItemGroup],"No match")')
    xl.add_column(cml, "EarlierYearInvoice",
                  '=XLOOKUP([@CreditMemoID],CreditMemo[CreditMemoID],CreditMemo[EarlierYearInvoice],"No match")')

    # (3) the quarterly grid
    periods = facts(b).periods()
    section(ws, "A4", f"Furniture revenue, fiscal {y}")
    for col, p in zip("BCDE", periods):
        text_cell(ws, f"{col}4", p)
    ws.Range("F4").Value = "Total"
    ws.Range("B4:F4").Font.Bold = True
    ws.Range("B4:F4").HorizontalAlignment = -4152
    labels = {5: "Gross Furniture revenue (InvoiceLines)", 6: "Furniture credit memo lines",
              7: "Net Furniture revenue", 9: "Furniture credit memo lines (count)",
              10: "Credits as a share of gross revenue"}
    for r, label in labels.items():
        ws.Cells(r, 1).Value = label
    for col in "BCDE":
        formulas(ws, {
            f"{col}5": f'=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],"Furniture",InvoiceLines[Period],{col}$4)',
            f"{col}6": (f'=SUMIFS(CreditMemoLine[LineTotal],CreditMemoLine[ItemGroup],"Furniture",'
                        f"CreditMemoLine[Period],{col}$4)"),
            f"{col}7": f"={col}5-{col}6",
            f"{col}9": f'=COUNTIFS(CreditMemoLine[ItemGroup],"Furniture",CreditMemoLine[Period],{col}$4)',
            f"{col}10": f"={col}6/{col}5"})
    for r in (5, 6, 7, 9):
        ws.Range(f"F{r}").Formula = f"=SUM(B{r}:E{r})"
    ws.Range("F10").Formula = "=F6/F5"
    ws.Range("A7:F7").Font.Bold = True
    ws.Range("B5:F7").NumberFormat = MONEY
    ws.Range("B9:F9").NumberFormat = COUNT
    ws.Range("B10:F10").NumberFormat = PCT
    values(ws, {"A12": "Credit memo lines not matched (CreditMemoDate, Period, ItemGroup)"})
    formulas(ws, {"B12": '=COUNTIF(CreditMemoLine[[CreditMemoDate]:[ItemGroup]],"No match")'})

    # (4) credits of the year for invoices of earlier years
    section(ws, "A14", f"Credits in {y} for invoices of earlier years (OriginalSalesInvoiceID)")
    values(ws, {"A15": "Credit memos", "A16": "Credit memo lines",
                "A17": "Furniture credits for invoices of earlier years",
                "A18": "Net Furniture revenue with those credits moved to the original invoice's year"})
    formulas(ws, {"B15": "=COUNTIF(CreditMemo[EarlierYearInvoice],TRUE)",
                  "B16": "=COUNTIF(CreditMemoLine[EarlierYearInvoice],TRUE)"})
    for col in "BCDE":
        formulas(ws, {f"{col}17": (f'=SUMIFS(CreditMemoLine[LineTotal],CreditMemoLine[ItemGroup],"Furniture",'
                                   f"CreditMemoLine[Period],{col}$4,CreditMemoLine[EarlierYearInvoice],TRUE)"),
                      f"{col}18": f"={col}7+{col}17"})
    for r in (17, 18):
        ws.Range(f"F{r}").Formula = f"=SUM(B{r}:E{r})"
    ws.Range("B17:F18").NumberFormat = MONEY
    top = 20
    header_row(ws, top, ["CreditMemoNumber", "CreditMemoDate", "OriginalInvoiceNumber", "OriginalInvoiceDate",
                         "SubTotal"])
    ws.Range(f"A{top + 1}").Formula2 = (
        "=SORT(FILTER(HSTACK(CreditMemo[CreditMemoNumber],CreditMemo[CreditMemoDate],CreditMemo[OriginalInvoiceNumber],"
        "CreditMemo[OriginalInvoiceDate],CreditMemo[SubTotal]),CreditMemo[EarlierYearInvoice]=TRUE),1)")
    n = len(f["earlier_list"])
    ws.Range(f"B{top + 1}:B{top + n}").NumberFormat = DATE
    ws.Range(f"D{top + 1}:D{top + n}").NumberFormat = DATE
    ws.Range(f"E{top + 1}:E{top + n}").NumberFormat = MONEY
    ws.Columns("A").ColumnWidth = 62
    ws.Columns("B:F").ColumnWidth = 18

    gross, credits, net = f["gross"], f["credits"], f["net"]
    q1, q3, q4 = periods[0], periods[2], periods[3]
    share = max(credits[p][1] / gross[p] for p in periods)
    memo_dates = sorted(m[1] for m in f["earlier_list"])
    inv_dates = sorted(m[3] for m in f["earlier_list"])
    moved = sum(f["earlier_furniture"].values())
    answer = (
        f"{word(f['earlier_memos']).capitalize()} credit memos dated in fiscal {y} ({f['earlier_lines']} lines, "
        f"{f['earlier_furniture_lines']} of them Furniture, {moved:,.2f}) reverse invoices issued in an earlier year: "
        f"the memos are dated {long_date(memo_dates[0], False)} to {long_date(memo_dates[-1])}, and their invoices "
        f"{long_date(inv_dates[0], False)} to {long_date(inv_dates[-1])}. For this analysis, assign each credit to the "
        "quarter of the credit memo: that is how the ledger records it, and it leaves the closed periods of the earlier "
        "year unchanged. Assigning credits to the original invoice's quarter measures the net sale more precisely, but "
        "it restates periods already closed; either is defensible if the schedule says which it uses. Here the choice "
        f"moves only {moved:,.2f} out of {q1}. The credits are small (at most {share:.1%} of gross Furniture revenue in "
        f"any quarter) and do not explain the change between {q3} and {q4}: net revenue falls by "
        f"{net[q3] - net[q4]:,.2f}, against {gross[q3] - gross[q4]:,.2f} gross.")
    model_answer(ws, top + n + 2, "Model answer, requirement (4)", answer, last="F")

    for col, p in zip("BCDE", periods):
        b.check(e, f"gross Furniture revenue {p} (Ex 5.1!{col}5)", round(gross[p], 2), f"='Ex 5.1'!{col}5")
        b.check(e, f"Furniture credit memo lines {p} (Ex 5.1!{col}6)", round(credits[p][1], 2), f"='Ex 5.1'!{col}6")
        b.check(e, f"net Furniture revenue {p} (Ex 5.1!{col}7)", round(net[p], 2), f"='Ex 5.1'!{col}7")
        b.check(e, f"Furniture credit memo line count {p} (Ex 5.1!{col}9)", credits[p][0], f"='Ex 5.1'!{col}9", 0, COUNT)
    b.check(e, f"Furniture credits, fiscal {y} (Ex 5.1!F6)", round(sum(c[1] for c in credits.values()), 2), "='Ex 5.1'!F6")
    b.check(e, f"Furniture credit memo lines, fiscal {y} (Ex 5.1!F9)", sum(c[0] for c in credits.values()),
            "='Ex 5.1'!F9", 0, COUNT)
    b.check(e, "credit memo lines not matched (Ex 5.1!B12)", f["unmatched"], "='Ex 5.1'!B12", 0, COUNT)
    b.check(e, f"credit memos of {y} for invoices of earlier years (Ex 5.1!B15)", f["earlier_memos"], "='Ex 5.1'!B15",
            0, COUNT)
    b.check(e, f"credit memo lines of {y} for invoices of earlier years (Ex 5.1!B16)", f["earlier_lines"],
            "='Ex 5.1'!B16", 0, COUNT)
    b.check(e, "Furniture credits for invoices of earlier years (Ex 5.1!F17)", round(moved, 2), "='Ex 5.1'!F17")
    b.check(e, "the earlier-year credit memos listed (first column of the list)",
            ", ".join(m[0] for m in f["earlier_list"]), f"=TEXTJOIN(\", \",TRUE,TAKE('Ex 5.1'!A{top + 1}#,,1))", 0, "General")


# --- Exercise 5.2 ------------------------------------------------------------------------------------------------------

def ex5_2(b: ExerciseBuild) -> None:
    wb, f, y, e = b.wb, facts(b).ex2, b.year, "5.2"
    ws = new_sheet(b, "Ex 5.2")
    heading(ws, e)
    inv = xl.table(wb, "SalesInvoice")
    # (1) and (2): the year in the number, as text and as a number, compared with the year of the InvoiceDate
    xl.add_column(inv, "NumberYearText", "=MID([@InvoiceNumber],4,4)")
    xl.add_column(inv, "NumberYear", "=VALUE([@NumberYearText])", "0")
    xl.add_column(inv, "NumberYearMatches", "=[@NumberYear]=YEAR([@InvoiceDate])")
    # (3): the order's date, and invoices dated before it
    xl.add_column(inv, "OrderDate", '=XLOOKUP([@SalesOrderID],SalesOrder[SalesOrderID],SalesOrder[OrderDate],"No match")',
                  DATE)
    xl.add_column(inv, "BeforeOrder", "=[@InvoiceDate]<[@OrderDate]")

    values(ws, {"A3": "Invoices whose number year differs from the year of the InvoiceDate",
                "A4": "Invoices dated before their order",
                "A5": "Invoices flagged by either test",
                "A6": "Invoices whose order was not found (OrderDate lookup)",
                "A7": "Sales orders whose number year differs from the year of the OrderDate",
                "A8": "Flagged invoices that are in the Tutorial 2.1 list",
                "A9": "Tutorial 2.1 invoices that neither test flags"})
    top = 11
    n21 = len(f["tutorial21"])
    t21 = f"$I${top + 1}:$I${top + n21}"
    formulas(ws, {"B3": "=COUNTIF(SalesInvoice[NumberYearMatches],FALSE)",
                  "B4": "=COUNTIF(SalesInvoice[BeforeOrder],TRUE)",
                  "B5": "=SUM(--(((SalesInvoice[NumberYearMatches]=FALSE)+(SalesInvoice[BeforeOrder]=TRUE))>0))",
                  "B6": '=COUNTIF(SalesInvoice[OrderDate],"No match")',
                  "B7": "=SUMPRODUCT(--(VALUE(MID(SalesOrder[OrderNumber],4,4))<>YEAR(SalesOrder[OrderDate])))",
                  "B8": f"=SUM(--G{top + 1}#)",
                  "B9": f"=SUM(--ISNA(XMATCH({t21},TAKE(A{top + 1}#,,1))))"})
    ws.Range("B3:B9").NumberFormat = COUNT

    # (4): the invoices flagged by either test, beside Tutorial 2.1's invoices dated before their first shipment
    header_row(ws, top, ["InvoiceNumber", "InvoiceDate", "OrderDate", "NumberYear", "NumberYearMatches", "BeforeOrder",
                         "In Tutorial 2.1 list"])
    ws.Range(f"A{top + 1}").Formula2 = (
        "=SORT(FILTER(HSTACK(SalesInvoice[InvoiceNumber],SalesInvoice[InvoiceDate],SalesInvoice[OrderDate],"
        "SalesInvoice[NumberYear],SalesInvoice[NumberYearMatches],SalesInvoice[BeforeOrder]),"
        "(SalesInvoice[NumberYearMatches]=FALSE)+(SalesInvoice[BeforeOrder]=TRUE)),1)")
    ws.Range(f"G{top + 1}").Formula2 = f"=ISNUMBER(XMATCH(TAKE(A{top + 1}#,,1),{t21}))"
    header_row(ws, top, ["Tutorial 2.1: InvoiceNumber", "InvoiceDate", "First ShipmentDate"], col=9)
    for i, (number, d, ship) in enumerate(f["tutorial21"]):
        r = top + 1 + i
        ws.Cells(r, 9).Value = number
        ws.Cells(r, 10).Value = serial(d)
        ws.Cells(r, 11).Value = serial(ship)
    note(ws, f"I{top}", "Typed from Tutorial 2.1: the invoices dated before the first shipment on their order, found with "
                        "MINIFS on the Shipment worksheet of CharlesRiver_Work.xlsx (Part I). This workbook does not load "
                        "the Shipment Table, so the list is entered as values, taken from the dataset when the companion "
                        "file was built.")
    rows = max(len(f["flagged"]), n21)
    ws.Range(f"B{top + 1}:C{top + rows}").NumberFormat = DATE
    ws.Range(f"J{top + 1}:K{top + rows}").NumberFormat = DATE
    ws.Columns("A").ColumnWidth = 62
    ws.Columns("B:G").ColumnWidth = 15
    ws.Columns("I").ColumnWidth = 26
    ws.Columns("J:K").ColumnWidth = 16

    p, o = f["prefix_rows"], f["order_rows"]
    years = sorted({r["date"][:4] for r in p})
    prefix_text = "; ".join(
        f"{series([r['number'] for r in p if r['date'][:4] == yy])} dated {long_date(min(r['date'] for r in p if r['date'][:4] == yy), False)}"
        f" to {long_date(max(r['date'] for r in p if r['date'][:4] == yy))}" for yy in years)
    answer4 = (
        f"{word(len(p)).capitalize()} invoices carry the next year's number ({prefix_text}), and "
        f"{word(len(o))} are dated before their order ({series(r['number'] for r in o)}, dated "
        f"{long_date(min(r['date'] for r in o), False)} to {long_date(max(r['date'] for r in o))}, a day before their orders). "
        f"Together they are exactly the {word(len(f['tutorial21']))} invoices Tutorial 2.1 found dated before their first "
        "shipment. The three findings point the same way: these invoices are dated earlier than the events they record. "
        f"The {word(len(p))} were numbered in the next year's sequence but dated in the year before, which suggests they "
        "were created after the year began and backdated into the earlier period, a revenue cutoff risk; the "
        f"{word(len(o))} are dated before the order was even placed. Sales order numbers always carry the year of their "
        "date, so the problem lies with how these invoices were dated, not with the numbering.")
    memo = (
        "To: Controller. From: Financial reporting analyst. Re: Invoices whose numbers or dates are inconsistent.\n"
        f"I tested all {f['invoices']:,} sales invoices two ways. First, I compared the year in each invoice number with "
        f"the year of its InvoiceDate: {word(len(p))} invoices differ, each carrying the next year's prefix (dated in "
        f"November and December, numbered in the following year). Second, I compared each InvoiceDate with the "
        f"OrderDate of its sales order: {word(len(o))} invoices are dated before their order. These "
        f"{word(len(f['flagged']))} invoices are the same ones dated before their first shipment in the data-quality "
        "review of Tutorial 2.1. The year in the invoice number is therefore reliable for every other invoice, but it "
        "cannot replace a test of the dates for these.\n"
        f"Effect on cutoff: the {word(len(p))} year-end invoices ({sum(r['subtotal'] for r in p):,.2f} of subtotal) "
        "are dated in one fiscal year and numbered in the next, and all of the flagged invoices are dated before their "
        "goods shipped, so their revenue may sit in the wrong period, whichever date the ledger follows. The amounts are "
        "small, but invoices dated ahead of the shipment at year-end are a cutoff control weakness. I would compare "
        "each invoice's posting date in the ledger with the shipment of its goods, and request from the billing team "
        "the invoice creation logs (who created each invoice and when), the shipping documents for the related orders, "
        "and the customers' acknowledgments of receipt, together with an explanation of how invoice dates are assigned.")
    r = top + rows + 2
    r = model_answer(ws, r, "Model answer, requirement (4)", answer4, last="G")
    model_answer(ws, r, "Model answer, requirement (5): memo to the controller", memo, last="G")

    b.check(e, "invoices whose number year differs (Ex 5.2!B3)", len(p), "='Ex 5.2'!B3", 0, COUNT)
    b.check(e, "invoices dated before their order (Ex 5.2!B4)", len(o), "='Ex 5.2'!B4", 0, COUNT)
    b.check(e, "invoices flagged by either test (Ex 5.2!B5)", len(f["flagged"]), "='Ex 5.2'!B5", 0, COUNT)
    b.check(e, "OrderDate lookups not matched (Ex 5.2!B6)", f["no_order"], "='Ex 5.2'!B6", 0, COUNT)
    b.check(e, "sales orders whose number year differs (Ex 5.2!B7)", f["order_mismatch"], "='Ex 5.2'!B7", 0, COUNT)
    b.check(e, "the flagged invoices (list, first column)", ", ".join(f["flagged"]),
            f"=TEXTJOIN(\", \",TRUE,TAKE('Ex 5.2'!A{top + 1}#,,1))", 0, "General")
    b.check(e, "flagged invoices in the Tutorial 2.1 list (Ex 5.2!B8)", f["in_t21"], "='Ex 5.2'!B8", 0, COUNT)
    b.check(e, "Tutorial 2.1 invoices neither test flags (Ex 5.2!B9)", f["t21_missed"], "='Ex 5.2'!B9", 0, COUNT)


# --- Exercise 5.3 ------------------------------------------------------------------------------------------------------

def ex5_3(b: ExerciseBuild) -> None:
    wb, f, e = b.wb, facts(b).ex3, "5.3"
    q3, q4 = f["q3"], f["q4"]
    ws = new_sheet(b, "Ex 5.3")
    heading(ws, e)
    ws.Range("A2").Value = "Period"
    text_cell(ws, "C2", q3)
    text_cell(ws, "E2", q4)
    ws.Range("C2:E2").Font.Bold = True
    header_row(ws, 3, ["Code", "Product type", f"{q3} revenue", f"{q3} quantity", f"{q4} revenue", f"{q4} quantity",
                       f"{q3} share", f"{q4} share", "Change in share"])
    crit = 'InvoiceLines[ItemGroup],"Furniture",InvoiceLines[ProductType],$A{r},InvoiceLines[Period],{p}'
    for i, (code, name) in enumerate(PRODUCT_TYPES):
        r = 4 + i
        values(ws, {f"A{r}": code, f"B{r}": name})
        formulas(ws, {f"C{r}": f"=SUMIFS(InvoiceLines[LineTotal],{crit.format(r=r, p='$C$2')})",
                      f"D{r}": f"=SUMIFS(InvoiceLines[Quantity],{crit.format(r=r, p='$C$2')})",
                      f"E{r}": f"=SUMIFS(InvoiceLines[LineTotal],{crit.format(r=r, p='$E$2')})",
                      f"F{r}": f"=SUMIFS(InvoiceLines[Quantity],{crit.format(r=r, p='$E$2')})",
                      f"G{r}": f"=C{r}/C$12", f"H{r}": f"=E{r}/E$12", f"I{r}": f"=H{r}-G{r}"})
    ws.Range("A12").Value = "Total"
    for col in "CDEFGHI":
        ws.Range(f"{col}12").Formula = f"=SUM({col}4:{col}11)"
    ws.Range("A12:I12").Font.Bold = True
    ws.Range("C4:F12").NumberFormat = MONEY
    ws.Range("G4:I12").NumberFormat = PCT
    values(ws, {"A14": "Highlight threshold (change in share)", "B14": SHARE_THRESHOLD,
                "A15": "Product types highlighted", "A16": "Furniture lines in the two quarters",
                "A17": "Of which with a fractional quantity"})
    ws.Range("B14").NumberFormat = PCT
    ws.Range("B14").Font.Color = xl.BLUE
    formulas(ws, {"B15": "=SUMPRODUCT(--(ABS(I4:I11)>B14))",
                  "B16": ('=COUNTIFS(InvoiceLines[ItemGroup],"Furniture",InvoiceLines[Period],C2)+'
                          'COUNTIFS(InvoiceLines[ItemGroup],"Furniture",InvoiceLines[Period],E2)'),
                  "B17": ('=COUNTIFS(InvoiceLines[ItemGroup],"Furniture",InvoiceLines[Period],C2,'
                          'InvoiceLines[WholeQuantity],FALSE)+COUNTIFS(InvoiceLines[ItemGroup],"Furniture",'
                          'InvoiceLines[Period],E2,InvoiceLines[WholeQuantity],FALSE)')})
    ws.Range("B15:B17").NumberFormat = COUNT
    # (3) highlight the product types whose share changed by more than the threshold
    ws.Activate()
    ws.Range("A4").Select()                      # a formula rule is read relative to the active cell
    rule = ws.Range("A4:I11").FormatConditions.Add(xl.XL_EXPRESSION, 1, "=ABS($I4)>$B$14")
    rule.Interior.Color = xl.LIGHT_FILL
    ws.Columns("A").ColumnWidth = 36
    ws.Columns("B").ColumnWidth = 16
    ws.Columns("C:I").ColumnWidth = 15

    grid, ch = f["grid"], f["change"]
    codes = [c for c, _ in PRODUCT_TYPES]
    change = {c: grid[c][q4][0] - grid[c][q3][0] for c in codes}
    losers = sorted((c for c in codes if change[c] < 0), key=lambda c: change[c])
    gainers = sorted((c for c in codes if change[c] > 0), key=lambda c: -change[c])
    largest = sorted(codes, key=lambda c: -abs(ch[c]))[:4]
    shifts = series(f"{PLURAL[c]} {100 * ch[c]:+.1f}" for c in
                    sorted((c for c in largest if ch[c] < 0), key=lambda c: ch[c]) +
                    sorted((c for c in largest if ch[c] >= 0), key=lambda c: -ch[c]))
    nh = f["highlighted"]
    answer = (
        f"Furniture revenue fell by {f['t3'] - f['t4']:,.2f} from {q3} to {q4}. {series(PLURAL[c] for c in losers[:2]).capitalize()} "
        f"lost the most revenue, while {series(PLURAL[c] for c in gainers[:2])} gained the most"
        + (f", and {series(PLURAL[c] for c in gainers[2:])} also gained" if gainers[2:] else "") +
        f". The largest changes in share were {shifts} percentage points. "
        + ("No product type moved by more than two points, so the rule highlights none: the mix shifted only modestly. "
           if nh == 0 else f"{word(nh).capitalize()} product types moved by more than two points and are highlighted. ") +
        f"Quantities need care: {f['fractional'] / f['lines']:.0%} of these Furniture lines carry a fractional quantity, "
        "even for items sold by the unit, so the quantities are not counts of whole products. Revenue shares do not "
        "depend on the quantity field, which makes them the more reliable measure of mix here.")
    model_answer(ws, 19, "Model answer, requirement (4)", answer)

    for i, (code, name) in enumerate(PRODUCT_TYPES):
        r = 4 + i
        g = grid[code]
        b.check(e, f"{code} revenue {q3} (Ex 5.3!C{r})", round(g[q3][0], 2), f"='Ex 5.3'!C{r}")
        b.check(e, f"{code} revenue {q4} (Ex 5.3!E{r})", round(g[q4][0], 2), f"='Ex 5.3'!E{r}")
        b.check(e, f"{code} quantity {q3} (Ex 5.3!D{r})", round(g[q3][1], 6), f"='Ex 5.3'!D{r}", 1e-6)
        b.check(e, f"{code} quantity {q4} (Ex 5.3!F{r})", round(g[q4][1], 6), f"='Ex 5.3'!F{r}", 1e-6)
    for code in largest:
        r = 4 + codes.index(code)
        b.check(e, f"{code} change in share (Ex 5.3!I{r})", round(ch[code], 9), f"='Ex 5.3'!I{r}", 1e-9, PCT)
    b.check(e, f"Furniture revenue {q3} (Ex 5.3!C12)", round(f["t3"], 2), "='Ex 5.3'!C12")
    b.check(e, f"Furniture revenue {q4} (Ex 5.3!E12)", round(f["t4"], 2), "='Ex 5.3'!E12")
    b.check(e, "product types highlighted (Ex 5.3!B15)", nh, "='Ex 5.3'!B15", 0, COUNT)
    b.check(e, "Furniture lines with a fractional quantity (Ex 5.3!B17)", f["fractional"], "='Ex 5.3'!B17", 0, COUNT)


# --- Exercise 5.4 ------------------------------------------------------------------------------------------------------

def ex5_4(b: ExerciseBuild) -> None:
    wb, f, y, e = b.wb, facts(b).ex4, b.year, "5.4"
    ws = new_sheet(b, "Ex 5.4")
    heading(ws, e)
    inv = xl.table(wb, "SalesInvoice")
    # (1) OrderDate came onto the SalesInvoice Table in Exercise 5.2; the lag in days
    xl.add_column(inv, "OrderToInvoiceDays", "=[@InvoiceDate]-[@OrderDate]", "0")
    days = "SalesInvoice[OrderToInvoiceDays]"
    section(ws, "A3", "Order-to-invoice lag, all invoices")
    values(ws, {"A4": "Invoices", "A5": "Average lag (days)", "A6": "Median lag (days)", "A7": "90th percentile (days)",
                "A8": "Invoices with a negative lag"})
    formulas(ws, {"B4": f"=COUNT({days})", "B5": f"=AVERAGE({days})", "B6": f"=MEDIAN({days})",
                  "B7": f"=PERCENTILE.INC({days},0.9)", "B8": f'=COUNTIF({days},"<0")'})
    ws.Range("B4").NumberFormat = COUNT
    ws.Range("B5:B7").NumberFormat = "0.0"
    ws.Range("B8").NumberFormat = COUNT
    # (2) by quarter of fiscal year y
    section(ws, "A10", f"Fiscal {y} by quarter of the InvoiceDate")
    header_row(ws, 11, ["Period", "Invoices", "Average lag (days)", "Median lag (days)"])
    periods = facts(b).periods()
    for i, p in enumerate(periods):
        r = 12 + i
        text_cell(ws, f"A{r}", p)
        formulas(ws, {f"B{r}": f"=COUNTIFS(SalesInvoice[Period],$A{r})",
                      f"C{r}": f"=AVERAGEIFS({days},SalesInvoice[Period],$A{r})",
                      f"D{r}": f"=MEDIAN(FILTER({days},SalesInvoice[Period]=$A{r}))"})
    values(ws, {"A16": "Range of the quarterly averages (days)"})
    ws.Range("C16").Formula = "=MAX(C12:C15)-MIN(C12:C15)"
    ws.Range("B12:B15").NumberFormat = COUNT
    ws.Range("C12:D16").NumberFormat = "0.0"
    # (3) promotion lines invoiced after the promotion's end date
    section(ws, "A18", "Promotion lines invoiced after the promotion's EffectiveEndDate")
    header_row(ws, 19, ["PromotionID", "PromotionCode", "EffectiveStartDate", "EffectiveEndDate", "Invoice lines",
                        "Invoiced after end date", "Share after end date"])
    formulas(ws, {"A20": "=PromotionProgram[PromotionID]", "B20": "=PromotionProgram[PromotionCode]",
                  "C20": "=PromotionProgram[EffectiveStartDate]", "D20": "=PromotionProgram[EffectiveEndDate]",
                  "E20": "=COUNTIFS(SalesInvoiceLine[PromotionID],A20#)",
                  "F20": '=COUNTIFS(SalesInvoiceLine[PromotionID],A20#,SalesInvoiceLine[InvoiceDate],">"&D20#)',
                  "G20": "=F20#/E20#"})
    n = len(f["promotions"])
    ws.Range(f"C20:D{19 + n}").NumberFormat = DATE
    ws.Range(f"E20:F{19 + n}").NumberFormat = COUNT
    ws.Range(f"G20:G{19 + n}").NumberFormat = "0.0%"
    ws.Columns("A").ColumnWidth = 40
    ws.Columns("B:G").ColumnWidth = 19

    qs = f["quarters"]
    means = [qs[p]["mean"] for p in periods]
    medians = [qs[p]["median"] for p in periods]
    fmt = lambda x: f"{x:g}"
    answer2 = (
        f"The median lag is {fmt(f['median'])} days and the average {f['mean']:.1f}. The average is higher because the "
        "distribution is skewed to the right: most orders are invoiced within a few weeks, but a minority take much "
        f"longer (the 90th percentile is {fmt(f['p90'])} days), and those long lags pull the average up while the median "
        f"is unaffected. The lag is stable: in fiscal {y} the quarterly averages run from {min(means):.1f} to "
        f"{max(means):.1f} days and the medians from {fmt(min(medians))} to {fmt(max(medians))}. "
        f"{word(f['negative']).capitalize()} invoices have a negative lag: they are dated before their order "
        "(Exercise 5.2).")
    every = [p for p in f["promotions"] if p["after"] == p["lines"] and p["lines"]]
    one_day = sum(1 for p in every if p["end"] == p["start"])
    backwards = sum(1 for p in every if p["end"] < p["start"])
    top = max(f["promotions"], key=lambda p: p["lines"])
    one_day_text = "a one-day promotion" if one_day == 1 else f"{word(one_day)} one-day promotions"
    memo = (
        "Assign promotional revenue by invoice date. Revenue is earned and recorded when the goods are invoiced, so the "
        "invoice date puts it in the right quarter and ties the analysis to the ledger. The order date explains the "
        "price: a promotional price is set when the order is placed, so promotion lines invoiced after a promotion ends "
        f"(for example {top['after']} of the {top['lines']} lines of {top['code']}) are not errors, and the order date "
        "should be used only to attribute those discounts to the promotion that caused them. Because the lag is stable "
        "from quarter to quarter, the share of a promotion's orders invoiced in the following quarter is predictable "
        "rather than a distortion of the comparison. "
        f"Promotions {series(p['code'][-3:] for p in every)} have every line invoiced after the end date because "
        f"their dates are wrong ({one_day_text} and {word(backwards)} whose end date precedes the start date), a "
        "master-data problem left for the audit analytics chapter (Chapter 8).")
    r = model_answer(ws, 21 + n, "Model answer, requirement (2)", answer2, last="G")
    model_answer(ws, r, "Model answer, requirement (4)", memo, last="G")

    b.check(e, "invoices with a lag (Ex 5.4!B4)", f["count"], "='Ex 5.4'!B4", 0, COUNT)
    b.check(e, "average lag, all invoices (Ex 5.4!B5)", round(f["mean"], 9), "='Ex 5.4'!B5", 1e-9, "0.0000")
    b.check(e, "median lag, all invoices (Ex 5.4!B6)", f["median"], "='Ex 5.4'!B6", 0, "0.0")
    b.check(e, "90th percentile of the lag (Ex 5.4!B7)", f["p90"], "='Ex 5.4'!B7", 1e-9, "0.0")
    b.check(e, "invoices with a negative lag (Ex 5.4!B8)", f["negative"], "='Ex 5.4'!B8", 0, COUNT)
    for i, p in enumerate(periods):
        r = 12 + i
        b.check(e, f"invoices {p} (Ex 5.4!B{r})", qs[p]["count"], f"='Ex 5.4'!B{r}", 0, COUNT)
        b.check(e, f"average lag {p} (Ex 5.4!C{r})", round(qs[p]["mean"], 9), f"='Ex 5.4'!C{r}", 1e-9, "0.0000")
        b.check(e, f"median lag {p} (Ex 5.4!D{r})", qs[p]["median"], f"='Ex 5.4'!D{r}", 0, "0.0")
    for p in f["promotions"]:
        code = p["code"]
        b.check(e, f"{code} invoice lines", p["lines"], f"=XLOOKUP(\"{code}\",'Ex 5.4'!B20#,'Ex 5.4'!E20#)", 0, COUNT)
        b.check(e, f"{code} lines invoiced after its end date", p["after"],
                f"=XLOOKUP(\"{code}\",'Ex 5.4'!B20#,'Ex 5.4'!F20#)", 0, COUNT)


# --- Exercise 5.5 ------------------------------------------------------------------------------------------------------

def ex5_5(b: ExerciseBuild) -> None:
    wb, f, e = b.wb, facts(b).ex5, "5.5"
    ws = new_sheet(b, "Ex 5.5")
    heading(ws, e)
    # (1) and (4): the three Tables (the exercise's "new workbook" is this file; see the cell note on A1)
    load(b, "Supplier", "Supplier", "Ex 5.5 Supplier", ws,
         extra=[("Removed Other Columns", select_in_order(SUPPLIER_COLUMNS))])
    load(b, "Employee", "Employee", "Ex 5.5 Employee", wb.Worksheets("Ex 5.5 Supplier"),
         extra=[("Removed Other Columns", select_in_order(EMPLOYEE_COLUMNS))])
    load(b, "DisbursementPayment", "DisbursementPayment", "Ex 5.5 DisbursementPayment", wb.Worksheets("Ex 5.5 Employee"))
    sup, emp = xl.table(wb, "Supplier"), xl.table(wb, "Employee")
    xl.table(wb, "DisbursementPayment").ListColumns("Amount").DataBodyRange.NumberFormat = MONEY
    for col in ("PaymentDate", "ClearedDate"):
        xl.table(wb, "DisbursementPayment").ListColumns(col).DataBodyRange.NumberFormat = DATE
    # (2) the match keys
    key = '=UPPER(TRIM([@Address])&", "&TRIM([@City]))'
    xl.add_column(emp, "MatchKey", key)
    xl.add_column(sup, "MatchKey", key)
    # (3) the matching employee; (4) the payments to each matched supplier
    look = '=IF([@EmployeeMatches]>0,XLOOKUP([@MatchKey],Employee[MatchKey],Employee[{c}]),"")'
    xl.add_column(sup, "EmployeeMatches", "=COUNTIFS(Employee[MatchKey],[@MatchKey])", "0")
    xl.add_column(sup, "MatchedEmployeeID", look.format(c="EmployeeID"), "0")
    xl.add_column(sup, "MatchedEmployee", look.format(c="EmployeeName"))
    xl.add_column(sup, "MatchedJobTitle", look.format(c="JobTitle"))
    xl.add_column(sup, "PaymentCount",
                  '=IF([@EmployeeMatches]>0,COUNTIFS(DisbursementPayment[SupplierID],[@SupplierID]),"")', COUNT)
    xl.add_column(sup, "PaymentTotal",
                  '=IF([@EmployeeMatches]>0,SUMIFS(DisbursementPayment[Amount],DisbursementPayment[SupplierID],'
                  '[@SupplierID]),"")', MONEY)
    note(ws, "A1", "Exercise 5.5 asks for a new workbook. This solution keeps all six exercises in one file, so the "
                   "Supplier, Employee, and DisbursementPayment Tables are the worksheets Ex 5.5 Supplier, Ex 5.5 "
                   "Employee, and Ex 5.5 DisbursementPayment. The Supplier query keeps the identifying and address "
                   "columns and also IsApproved and SupplierRiskRating, which Exercise 5.6 uses; the Employee query "
                   "also keeps JobTitle, which requirement (3) brings onto the Supplier Table.")

    values(ws, {"A3": "Suppliers whose match key appears in the Employee Table",
                "A4": "Matches on Address and City as recorded (without TRIM and UPPER)",
                "A5": "Payments to the matched suppliers (count)",
                "A6": "Payments to the matched suppliers (amount)"})
    formulas(ws, {"B3": '=COUNTIF(Supplier[EmployeeMatches],">0")',
                  "B4": "=SUMPRODUCT(--(COUNTIFS(Employee[Address],Supplier[Address],Employee[City],Supplier[City])>0))",
                  "B5": "=SUM(Supplier[PaymentCount])", "B6": "=SUM(Supplier[PaymentTotal])"})
    ws.Range("B3:B5").NumberFormat = COUNT
    ws.Range("B6").NumberFormat = MONEY
    top = 8
    header_row(ws, top, ["SupplierID", "SupplierName", "EmployeeID", "EmployeeName", "JobTitle", "Payments",
                         "Amount paid"])
    ws.Range(f"A{top + 1}").Formula2 = (
        "=FILTER(HSTACK(Supplier[SupplierID],Supplier[SupplierName],Supplier[MatchedEmployeeID],Supplier[MatchedEmployee],"
        "Supplier[MatchedJobTitle],Supplier[PaymentCount],Supplier[PaymentTotal]),Supplier[EmployeeMatches]>0)")
    m = f["matches"]
    ws.Range(f"F{top + 1}:F{top + len(m)}").NumberFormat = COUNT
    ws.Range(f"G{top + 1}:G{top + len(m)}").NumberFormat = MONEY
    ws.Columns("A").ColumnWidth = 58
    ws.Columns("B").ColumnWidth = 30
    ws.Columns("C").ColumnWidth = 12
    ws.Columns("D:E").ColumnWidth = 20
    ws.Columns("F:G").ColumnWidth = 15

    answer2 = (
        "The key includes the city because a street address is not unique on its own: the same number and street name "
        "can exist in different towns, so a key on the address alone could match a supplier with an unrelated employee "
        "(a false positive). Joining the city makes the key identify one location. TRIM and UPPER make the comparison "
        "ignore extra spaces and differences in case, so a match is not hidden by how the address was typed. In this "
        f"data the addresses match exactly: the raw Address and City find the same {word(f['raw'])} suppliers, so "
        "standardizing does not change the result, which is itself worth recording in the workpapers.")
    lines = "; ".join(f"supplier {x['id']} {x['name']} and employee {x['emp']} {x['emp_name']} ({x['title']}), "
                      f"{x['payments']:,} payments of {x['paid']:,.2f}" for x in m)
    total_n, total_paid = sum(x["payments"] for x in m), sum(x["paid"] for x in m)
    distinct = sorted({x["title"] for x in m})
    assert not any(w in t.lower() for t in distinct for w in ("purchas", "buyer", "procure")), distinct
    counts = {t: sum(x["title"] == t for x in m) for t in distinct}
    titles = series(f"{word(counts[t])} {t}s" if counts[t] > 1 else ("an " if t[0] in "AEIOU" else "a ") + t
                    for t in sorted(distinct, key=lambda t: -counts[t]))
    memo = (
        "To: Audit senior. Re: Suppliers that share an address with an employee.\n"
        f"I matched every supplier's address and city with the employee master file, after standardizing both with TRIM "
        f"and UPPER. {word(len(m)).capitalize()} suppliers share an exact address and city with an employee: {lines}. "
        f"Together they received {total_n:,} payments totaling {total_paid:,.2f}. A shared address does not prove a "
        "related party or a fictitious vendor, but it is a recognized red flag; the employees involved are "
        f"{titles}, none of them in purchasing, so each relationship needs explaining.\n"
        "Next procedures: confirm the ownership of each supplier (business registrations, the tax identification "
        "number, and an inquiry of the employee); review who approved each supplier's setup and its invoices, and "
        "whether the employee had any part in that; compare the prices charged with those of other suppliers of the "
        "same items; and test a sample of the payments for evidence that the goods or services were received.")
    r = top + len(m) + 2
    r = model_answer(ws, r, "Model answer, requirement (2)", answer2, last="G")
    model_answer(ws, r, "Model answer, requirement (5): memo to the audit senior", memo, last="G")

    b.check(e, "suppliers sharing an address and city with an employee (Ex 5.5!B3)", len(m), "='Ex 5.5'!B3", 0, COUNT)
    b.check(e, "matches on the address and city as recorded (Ex 5.5!B4)", f["raw"], "='Ex 5.5'!B4", 0, COUNT)
    b.check(e, "each matched supplier shares its address with one employee", len(m),
            '=COUNTIF(Supplier[EmployeeMatches],1)', 0, COUNT)
    for x in m:
        sid = x["id"]
        get = lambda col: f"=XLOOKUP({sid},Supplier[SupplierID],Supplier[{col}])"
        b.check(e, f"supplier {sid}: matched employee", x["emp_name"], get("MatchedEmployee"), 0, "General")
        b.check(e, f"supplier {sid}: matched employee's job title", x["title"], get("MatchedJobTitle"), 0, "General")
        b.check(e, f"supplier {sid}: payments", x["payments"], get("PaymentCount"), 0, COUNT)
        b.check(e, f"supplier {sid}: amount paid", round(x["paid"], 2), get("PaymentTotal"))
    b.check(e, "payments to the matched suppliers (Ex 5.5!B6)", round(total_paid, 2), "='Ex 5.5'!B6")


# --- Exercise 5.6 ------------------------------------------------------------------------------------------------------

def ex5_6(b: ExerciseBuild) -> None:
    wb, f, e = b.wb, facts(b).ex6, "5.6"
    ws = new_sheet(b, "Ex 5.6")
    heading(ws, e)
    sup = xl.table(wb, "Supplier")
    # (1) PROPER, and the names it changes
    xl.add_column(sup, "ProperName", "=PROPER([@SupplierName])")
    xl.add_column(sup, "NameChanged", "=NOT(EXACT([@ProperName],[@SupplierName]))")
    # (2) shared identifiers, counted with an exact comparison (the masked BankAccount values start with asterisks,
    # which COUNTIF would read as wildcards)
    xl.add_column(sup, "TaxIDCount", "=SUM(--(Supplier[TaxID]=[@TaxID]))", "0")
    xl.add_column(sup, "BankAccountCount", "=SUM(--(Supplier[BankAccount]=[@BankAccount]))", "0")
    # (4) the purchase orders
    load(b, "PurchaseOrder", "PurchaseOrder", "Ex 5.6 PurchaseOrder", ws)
    po = xl.table(wb, "PurchaseOrder")
    po.ListColumns("OrderTotal").DataBodyRange.NumberFormat = MONEY
    for col in ("OrderDate", "ExpectedDeliveryDate"):
        po.ListColumns(col).DataBodyRange.NumberFormat = DATE
    # (5) the item master, tested against the invoice lines
    load(b, "ItemMaster", "Item", "Ex 5.6 ItemMaster", wb.Worksheets("Ex 5.6 PurchaseOrder"))
    im = xl.table(wb, "ItemMaster")
    im.ListColumns("LaunchDate").DataBodyRange.NumberFormat = DATE
    xl.add_column(im, "InvoiceLineCount", "=COUNTIFS(SalesInvoiceLine[ItemID],[@ItemID])", COUNT)
    xl.add_column(im, "LatestInvoiceDate",
                  '=IF([@InvoiceLineCount]>0,MAXIFS(SalesInvoiceLine[InvoiceDate],SalesInvoiceLine[ItemID],[@ItemID]),"")',
                  DATE)
    lines = xl.table(wb, "SalesInvoiceLine")
    xl.add_column(lines, "LaunchDate", '=XLOOKUP([@ItemID],ItemMaster[ItemID],ItemMaster[LaunchDate],"No match")', DATE)
    xl.add_column(lines, "BeforeLaunch", "=[@InvoiceDate]<[@LaunchDate]")
    xl.add_column(im, "PrelaunchLines", "=COUNTIFS(SalesInvoiceLine[ItemID],[@ItemID],SalesInvoiceLine[BeforeLaunch],TRUE)",
                  COUNT)
    note(ws, "A1", "The supplier tests use the Supplier Table of Exercise 5.5 (worksheet Ex 5.5 Supplier), which kept "
                   "IsApproved and SupplierRiskRating for this exercise. The shared-identifier counts compare values "
                   "with = rather than COUNTIF, because the masked BankAccount values begin with asterisks, which "
                   "COUNTIF reads as wildcards.")

    section(ws, "A3", "Supplier master file")
    values(ws, {"A4": "Supplier names PROPER changes", "A5": "Suppliers",
                "A6": "Suppliers that share a TaxID", "A7": "Suppliers that share a BankAccount",
                "A8": "Unapproved suppliers (IsApproved 0)",
                "A9": "Purchase orders and payments of the unapproved suppliers",
                "A10": "High-risk suppliers (SupplierRiskRating High)",
                "A11": "High-risk suppliers approved, with purchase orders and payments"})
    section(ws, "A13", "Item master file")
    values(ws, {"A14": "Items Discontinued but IsActive 1", "A15": "Items with IsActive 0 still invoiced",
                "A16": "Invoice lines dated before their item's LaunchDate", "A17": "Their line total",
                "A18": "LaunchDate lookups not matched"})
    # the lists, each below the last
    u0 = 20
    nu = len(f["unapproved"])
    h0 = u0 + nu + 3
    nh = len(f["high"])
    c0 = h0 + nh + 3
    nc = len(f["conflict"])
    i0 = c0 + nc + 3
    ni = len(f["inactive"])
    p0 = i0 + ni + 3
    np_ = len(f["prelaunch"])
    supplier_cols = ["SupplierID", "SupplierName", "SupplierRiskRating", "IsApproved", "Purchase orders", "Payments"]
    for top, title, cond in ((u0, "Unapproved suppliers, with their purchase orders and payments", "Supplier[IsApproved]=0"),
                             (h0, "High-risk suppliers, with their purchase orders and payments",
                              'Supplier[SupplierRiskRating]="High"')):
        section(ws, f"A{top - 1}", title)
        header_row(ws, top, supplier_cols)
        formulas(ws, {
            f"A{top + 1}": ("=FILTER(HSTACK(Supplier[SupplierID],Supplier[SupplierName],Supplier[SupplierRiskRating],"
                            f"Supplier[IsApproved]),{cond})"),
            f"E{top + 1}": f"=COUNTIFS(PurchaseOrder[SupplierID],TAKE(A{top + 1}#,,1))",
            f"F{top + 1}": f"=COUNTIFS(DisbursementPayment[SupplierID],TAKE(A{top + 1}#,,1))"})
    section(ws, f"A{c0 - 1}", "Items Discontinued but IsActive 1")
    header_row(ws, c0, ["ItemID", "ItemCode", "ItemName", "LifecycleStatus", "IsActive", "Invoice lines"])
    ws.Range(f"A{c0 + 1}").Formula2 = (
        "=FILTER(HSTACK(ItemMaster[ItemID],ItemMaster[ItemCode],ItemMaster[ItemName],ItemMaster[LifecycleStatus],"
        'ItemMaster[IsActive],ItemMaster[InvoiceLineCount]),(ItemMaster[LifecycleStatus]="Discontinued")*'
        "(ItemMaster[IsActive]=1))")
    section(ws, f"A{i0 - 1}", "Items with IsActive 0 that were still invoiced")
    header_row(ws, i0, ["ItemID", "ItemCode", "ItemName", "LifecycleStatus", "IsActive", "Invoice lines",
                        "Latest InvoiceDate"])
    ws.Range(f"A{i0 + 1}").Formula2 = (
        "=FILTER(HSTACK(ItemMaster[ItemID],ItemMaster[ItemCode],ItemMaster[ItemName],ItemMaster[LifecycleStatus],"
        "ItemMaster[IsActive],ItemMaster[InvoiceLineCount],ItemMaster[LatestInvoiceDate]),(ItemMaster[IsActive]=0)*"
        "(ItemMaster[InvoiceLineCount]>0))")
    ws.Range(f"G{i0 + 1}:G{i0 + ni}").NumberFormat = DATE
    section(ws, f"A{p0 - 1}", "Items invoiced before their LaunchDate, counted by item")
    header_row(ws, p0, ["ItemID", "ItemCode", "ItemName", "LaunchDate", "Lines before launch", "First InvoiceDate",
                        "Last InvoiceDate", "Line total"])
    pre = f"TAKE(A{p0 + 1}#,,1)"
    formulas(ws, {
        f"A{p0 + 1}": ("=FILTER(HSTACK(ItemMaster[ItemID],ItemMaster[ItemCode],ItemMaster[ItemName],ItemMaster[LaunchDate],"
                       "ItemMaster[PrelaunchLines]),ItemMaster[PrelaunchLines]>0)"),
        f"F{p0 + 1}": f"=MINIFS(SalesInvoiceLine[InvoiceDate],SalesInvoiceLine[ItemID],{pre},SalesInvoiceLine[BeforeLaunch],TRUE)",
        f"G{p0 + 1}": f"=MAXIFS(SalesInvoiceLine[InvoiceDate],SalesInvoiceLine[ItemID],{pre},SalesInvoiceLine[BeforeLaunch],TRUE)",
        f"H{p0 + 1}": f"=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[ItemID],{pre},SalesInvoiceLine[BeforeLaunch],TRUE)"})
    ws.Range(f"D{p0 + 1}:D{p0 + np_}").NumberFormat = DATE
    ws.Range(f"F{p0 + 1}:G{p0 + np_}").NumberFormat = DATE
    ws.Range(f"H{p0 + 1}:H{p0 + np_}").NumberFormat = MONEY
    # the summary counts above the lists
    formulas(ws, {"B4": "=COUNTIF(Supplier[NameChanged],TRUE)", "B5": "=ROWS(Supplier[SupplierID])",
                  "B6": '=COUNTIF(Supplier[TaxIDCount],">1")', "B7": '=COUNTIF(Supplier[BankAccountCount],">1")',
                  "B8": "=COUNTIF(Supplier[IsApproved],0)", "B9": f"=SUM(E{u0 + 1}#)+SUM(F{u0 + 1}#)",
                  "B10": '=COUNTIF(Supplier[SupplierRiskRating],"High")',
                  "B11": f"=SUM((CHOOSECOLS(A{h0 + 1}#,4)=1)*(E{h0 + 1}#>0)*(F{h0 + 1}#>0))",
                  "B14": '=COUNTIFS(ItemMaster[LifecycleStatus],"Discontinued",ItemMaster[IsActive],1)',
                  "B15": '=COUNTIFS(ItemMaster[IsActive],0,ItemMaster[InvoiceLineCount],">0")',
                  "B16": "=COUNTIF(SalesInvoiceLine[BeforeLaunch],TRUE)",
                  "B17": "=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[BeforeLaunch],TRUE)",
                  "B18": '=COUNTIF(SalesInvoiceLine[LaunchDate],"No match")'})
    ws.Range("B4:B16").NumberFormat = COUNT
    ws.Range("B17").NumberFormat = MONEY
    ws.Range("B18").NumberFormat = COUNT
    ws.Columns("A").ColumnWidth = 58
    ws.Columns("B").ColumnWidth = 30
    ws.Columns("C").ColumnWidth = 32
    ws.Columns("D:H").ColumnWidth = 17

    # model answers, then the long list of the names PROPER changes
    ch, words = f["changed"], f["words"]
    lowered = sorted((w for w in words if w.isupper()), key=lambda w: -words[w])
    answer1 = (
        f"PROPER changes {len(ch)} of the {f['suppliers']} supplier names, for example \"Watson, Mitchell and Chen\" to "
        "\"Watson, Mitchell And Chen\" and \"Donaldson LLC\" to \"Donaldson Llc\". "
        f"Every change capitalizes the connecting word \"and\" or lowers an abbreviation ({series(lowered)}): the names "
        "are already consistently cased, so PROPER would only damage them. Standardizing is useful when a field is "
        "inconsistent; here the right step is to leave the names as they are and record that they were checked (a "
        "matching key can use UPPER without changing the names).")
    answer2 = (
        f"No TaxID and no BankAccount is shared by two suppliers, so the master file holds no duplicate suppliers on "
        "these keys. The clean result shows only that no two records carry the same identifier. It does not show that "
        "there are no duplicates: a supplier entered twice with a different, mistyped, or missing tax ID or bank "
        "account would not be caught, and both fields are partly masked in this extract. A test on names and addresses "
        "(as in Exercise 5.5) would complement it.")
    un, hi = f["unapproved"], f["high"]
    hi_ok = [s for s in hi if s["approved"] == 1 and s["po"] > 0 and s["pay"] > 0]
    hi_un = [s for s in hi if s["approved"] == 0]
    inactive, prelaunch = f["inactive"], f["prelaunch"]
    latest = sorted({x["latest"] for x in inactive})
    inactive_text = "; ".join(f"{x['code']}, {x['lines']} lines" for x in inactive)
    prelaunch_text = "; ".join(f"{p['code']}, {p['lines']} lines from {p['first']} to {p['last']}" for p in prelaunch)
    memo = (
        "To: Audit senior. Re: Review of the supplier and item master files.\n"
        f"Supplier master: the names are consistently cased, and PROPER would damage {len(ch)} of {f['suppliers']}, so "
        "they were left unchanged. No TaxID or BankAccount is shared, so there are no duplicate suppliers on those keys. "
        f"{word(len(un)).capitalize()} suppliers are unapproved (IDs {un[0]['id']} to {un[-1]['id']}), and none has a "
        "purchase order or a payment, so the approval control appears to work. "
        f"{word(len(hi)).capitalize()} suppliers are rated High risk (IDs {series(s['id'] for s in hi)}); "
        f"{word(len(hi_ok))} of them are approved and receiving business"
        + (f", and {series(s['id'] for s in hi_un)} is also unapproved" if hi_un else "") + ". "
        f"I recommend that the purchasing tests focus on the {word(len(hi_ok))} approved High-risk suppliers and on the "
        "six suppliers that share an address with an employee (Exercise 5.5), with larger samples of their invoices "
        "and payments.\n"
        f"Item master: {word(len(f['conflict']))} items are Discontinued but still flagged active (IDs "
        f"{series(i for i, _ in f['conflict'])}: {series(c for _, c in f['conflict'])}), a status conflict that means the "
        f"two fields cannot both be right. {word(len(inactive)).capitalize()} inactive, Discontinued items were still "
        f"invoiced, through {long_date(latest[-1])} ({inactive_text}), "
        f"so the inactive flag does not stop sales. {word(len(prelaunch)).capitalize()} items were invoiced before their "
        f"LaunchDate ({prelaunch_text}; "
        f"{sum(p['lines'] for p in prelaunch)} lines and {sum(p['amount'] for p in prelaunch):,.2f} in all), so the "
        "launch dates are wrong or sales were recorded before launch. Together, the findings mean the status and launch "
        "fields cannot be relied on to control sales; the item master needs a review of who maintains these fields, "
        "and the sales tests should not use them to define their populations.")
    r = p0 + np_ + 2
    r = model_answer(ws, r, "Model answer, requirement (1)", answer1, last="H")
    r = model_answer(ws, r, "Model answer, requirement (2)", answer2, last="H")
    r = model_answer(ws, r, "Model answer, requirement (6): memo to the audit senior", memo, last="H")
    section(ws, f"A{r}", "Supplier names PROPER changes")
    header_row(ws, r + 1, ["SupplierName", "PROPER(SupplierName)"])
    ws.Range(f"A{r + 2}").Formula2 = "=FILTER(HSTACK(Supplier[SupplierName],Supplier[ProperName]),Supplier[NameChanged])"
    names_top = r + 2

    ids = lambda rows: ", ".join(str(s["id"]) for s in rows)
    b.check(e, "supplier names PROPER changes (Ex 5.6!B4)", len(ch), "='Ex 5.6'!B4", 0, COUNT)
    b.check(e, "suppliers (Ex 5.6!B5)", f["suppliers"], "='Ex 5.6'!B5", 0, COUNT)
    first, changed_to = ch[0][0], ch[0][1].replace('"', '""')
    b.check(e, f"PROPER turns {first} into {ch[0][1]} (EXACT, case-sensitive)", True,
            f"=EXACT(INDEX('Ex 5.6'!A{names_top}#,1,2),\"{changed_to}\")", 0, "General")
    b.check(e, "suppliers that share a TaxID (Ex 5.6!B6)", f["tax_shared"], "='Ex 5.6'!B6", 0, COUNT)
    b.check(e, "suppliers that share a BankAccount (Ex 5.6!B7)", f["bank_shared"], "='Ex 5.6'!B7", 0, COUNT)
    b.check(e, "unapproved suppliers (Ex 5.6!B8)", len(un), "='Ex 5.6'!B8", 0, COUNT)
    b.check(e, "unapproved suppliers' IDs (list)", ids(un), f"=TEXTJOIN(\", \",TRUE,TAKE('Ex 5.6'!A{u0 + 1}#,,1))", 0, "General")
    b.check(e, "purchase orders and payments of unapproved suppliers (Ex 5.6!B9)", sum(s["po"] + s["pay"] for s in un),
            "='Ex 5.6'!B9", 0, COUNT)
    b.check(e, "High-risk suppliers (Ex 5.6!B10)", len(hi), "='Ex 5.6'!B10", 0, COUNT)
    b.check(e, "High-risk suppliers' IDs (list)", ids(hi), f"=TEXTJOIN(\", \",TRUE,TAKE('Ex 5.6'!A{h0 + 1}#,,1))", 0, "General")
    b.check(e, "High-risk suppliers approved and receiving business (Ex 5.6!B11)", len(hi_ok), "='Ex 5.6'!B11", 0, COUNT)
    b.check(e, "items Discontinued but IsActive 1 (Ex 5.6!B14)", len(f["conflict"]), "='Ex 5.6'!B14", 0, COUNT)
    b.check(e, "their item codes (list)", ", ".join(c for _, c in f["conflict"]),
            f"=TEXTJOIN(\", \",TRUE,INDEX('Ex 5.6'!A{c0 + 1}#,0,2))", 0, "General")
    b.check(e, "items with IsActive 0 still invoiced (Ex 5.6!B15)", len(inactive), "='Ex 5.6'!B15", 0, COUNT)
    for x in inactive:
        get = lambda col: f"=XLOOKUP({x['id']},ItemMaster[ItemID],ItemMaster[{col}])"
        b.check(e, f"{x['code']}: invoice lines", x["lines"], get("InvoiceLineCount"), 0, COUNT)
        b.check(e, f"{x['code']}: latest InvoiceDate", serial(x["latest"]), get("LatestInvoiceDate"), 0, DATE)
    b.check(e, "invoice lines dated before their item's launch (Ex 5.6!B16)", sum(p["lines"] for p in prelaunch),
            "='Ex 5.6'!B16", 0, COUNT)
    b.check(e, "their line total (Ex 5.6!B17)", round(sum(p["amount"] for p in prelaunch), 2), "='Ex 5.6'!B17")
    for p in prelaunch:
        get = lambda col: f"=XLOOKUP({p['id']},ItemMaster[ItemID],ItemMaster[{col}])"
        row = lambda k: f"=XLOOKUP({p['id']},TAKE('Ex 5.6'!A{p0 + 1}#,,1),'Ex 5.6'!{k}{p0 + 1}#)"
        b.check(e, f"{p['code']}: lines before launch", p["lines"], get("PrelaunchLines"), 0, COUNT)
        b.check(e, f"{p['code']}: first InvoiceDate before launch", serial(p["first"]), row("F"), 0, DATE)
        b.check(e, f"{p['code']}: last InvoiceDate before launch", serial(p["last"]), row("G"), 0, DATE)
    for i in f["extra"]:
        b.check(e, f"item {i} (in the AnomalyLog's prelaunch items): lines before launch", f["extra_lines"][i],
                f"=XLOOKUP({i},ItemMaster[ItemID],ItemMaster[PrelaunchLines])", 0, COUNT)
    b.check(e, "LaunchDate lookups not matched (Ex 5.6!B18)", 0, "='Ex 5.6'!B18", 0, COUNT)


EXERCISES = [("5.1", ex5_1), ("5.2", ex5_2), ("5.3", ex5_3), ("5.4", ex5_4), ("5.5", ex5_5), ("5.6", ex5_6)]
