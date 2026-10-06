"""Charles River Furniture Analysis.xlsx: the workbook Tutorials 4.1 to 7.3 build.

Each function applies one tutorial's steps to the workbook as the previous tutorial left it: the same queries (with the
Power Query Editor's step names), worksheets, cell addresses, formulas, names, and formats the tutorial text gives.
Where a step only shows the reader something (a slicer clicked, a filter tried and cleared), the end state is built.
Each tutorial also adds its checks to the Solution Notes: the control totals its checkpoint asks for, with the value
the dataset gives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from xlbuild import expected, pq, xl
from xlbuild.expected import GROUPS, METHODS, RATES, Expected
from xlbuild.notes import Check

FILE = "Charles River Furniture Analysis.xlsx"
PROMO = 8                  # the promotion the tutorials name (Tutorial 4.3); asserted to be the one with most lines
YEAR_END_CLOSE = "JE-{year}-000296"   # the closing entry Tutorial 7.2 excludes (the Part I case found it)
ITEM_COLUMNS = ["ItemID", "ItemCode", "ItemName", "ItemGroup", "ItemType", "StandardCost", "ListPrice",
                "UnitOfMeasure", "SupplyMode", "CollectionName", "LifecycleStatus"]
MONEY, COUNT, RATIO, PCT = "#,##0.00", "#,##0", "0.0000", "0.00%"


@dataclass
class Build:
    wb: object
    src: str                                    # the CharlesRiver.xlsx path the queries read while building
    xlsx: Path                                  # the same workbook, for type detection
    exp: Expected
    year: int                                   # the report year (fiscal 2026 in the 2026 edition)
    checks: list = field(default_factory=list)  # (tutorial, Check)
    doc: dict = field(default_factory=dict)     # the Documentation worksheet's entries
    sheets: dict = field(default_factory=dict)  # worksheet -> what it holds
    queries: dict = field(default_factory=dict)  # query -> its steps, for queries that later tutorials extend
    extra: list = field(default_factory=list)    # Documentation entries after the eleven labels: [label, text]
    found: dict = field(default_factory=dict)    # values a tutorial records for a later step (Goal Seek's lift)

    def check(self, tutorial: str, label: str, expected, actual: str, tolerance: float = 0.005, fmt: str = MONEY):
        self.checks.append((tutorial, Check(label, expected, actual, tolerance, fmt)))


def long_date(iso: str, year: bool = True) -> str:
    """2026-09-01 as the book writes it: September 1, 2026 (or September 1)."""
    import calendar
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{calendar.month_name[m]} {d}" + (f", {y}" if year else "")


def nav(b: Build, number: int, table: str, corrections: dict | None = None, extra=()) -> str:
    return pq.navigator_query(b.src, number, table, list(pq.detected_types(b.xlsx, table)), corrections, list(extra))


def ws_(b: Build, name: str):
    return b.wb.Worksheets(name)


def formulas(ws, cells: dict[str, str]) -> None:
    for addr, f in cells.items():
        ws.Range(addr).Formula2 = f


def values(ws, cells: dict[str, object]) -> None:
    for addr, v in cells.items():
        ws.Range(addr).Value = v


def write_documentation(b: Build) -> None:
    labels = ["Purpose", "Source", "Query steps", "Last refreshed", "Parameters", "Calculated columns", "Worksheets",
              "Conventions", "Prepared by", "Reviewed by", "Open questions"]
    ws = ws_(b, "Documentation")
    ws.Cells.Clear()
    order = [s.Name for s in b.wb.Worksheets if s.Name in b.sheets]
    b.doc["Worksheets"] = "; ".join(f"{s}: {b.sheets[s]}" for s in order)
    b.doc["Last refreshed"] = "'" + pq.today()          # text, so Excel does not turn it into a date
    rows = [(label, b.doc.get(label, "")) for label in labels] + [tuple(x) for x in b.extra]
    for i, (label, text) in enumerate(rows, start=1):
        ws.Cells(i, 1).Value = label
        ws.Cells(i, 2).Value = text
    ws.Columns("A").Font.Bold = True
    ws.Columns("A").ColumnWidth = 20
    ws.Columns("B").ColumnWidth = 110
    ws.Columns("B").WrapText = True
    ws.Columns("A:B").VerticalAlignment = -4160
    ws.Rows.AutoFit()


# --- Chapter 4 -----------------------------------------------------------------------------------------------------

def t4_1(b: Build) -> None:
    wb, e = b.wb, b.exp
    dates = {c: "type date" for c in ("InvoiceDate", "DueDate", "PaymentDate")}
    xl.add_query(wb, "SalesInvoice", nav(b, 16, "SalesInvoice", {**dates, "FreightAmount": "type number"}))
    xl.add_query(wb, "SalesInvoiceLine", nav(b, 17, "SalesInvoiceLine", {"Discount": "type number"}))
    xl.add_query(wb, "Item", nav(b, 44, "Item", extra=[
        ("Filtered Rows", "Table.SelectRows({prev}, each ([ListPrice] <> null))"),
        ("Removed Other Columns", pq.select_columns(ITEM_COLUMNS))]))
    xl.add_query(wb, "PromotionProgram", nav(b, 7, "PromotionProgram"))
    blank = wb.Worksheets(1)
    for name in ("SalesInvoice", "SalesInvoiceLine", "Item", "PromotionProgram"):
        xl.load_query(wb, name, name)
    blank.Delete()

    lines = xl.table(wb, "SalesInvoiceLine")
    xl.add_column(lines, "ListAmount", "=ROUND([@Quantity]*[@BaseListPrice],2)")
    xl.add_column(lines, "DiscountAmount", "=ROUND([@Quantity]*[@UnitPrice]*[@Discount],2)")

    ws = xl.sheet(wb, "Analysis")
    values(ws, {"A1": "Control totals", "A3": "Invoice lines", "A4": "Invoices", "A5": "Line total",
                "A6": "Invoice subtotal", "A7": "Difference", "A8": "Discount taken", "A9": "List amount"})
    formulas(ws, {"B3": "=COUNTA(SalesInvoiceLine[SalesInvoiceLineID])", "B4": "=COUNTA(SalesInvoice[SalesInvoiceID])",
                  "B5": "=SUM(SalesInvoiceLine[LineTotal])", "B6": "=SUM(SalesInvoice[SubTotal])",
                  "B7": "=ROUND(B5-B6,2)", "B8": "=SUM(SalesInvoiceLine[DiscountAmount])",
                  "B9": "=SUM(SalesInvoiceLine[ListAmount])"})
    ws.Range("B5:B9").NumberFormat = MONEY
    ws.Columns("A").ColumnWidth = 30
    ws.Columns("B").ColumnWidth = 16

    b.sheets.update(SalesInvoice="the invoices (query SalesInvoice)", SalesInvoiceLine="the invoice lines (query SalesInvoiceLine) "
                    "with two calculated columns", Item="the items Charles River sells (query Item)",
                    PromotionProgram="the promotion programs (query PromotionProgram)", Analysis="control totals")
    c = e.control
    t = "4.1"
    b.check(t, "items with a list price (rows of the Item Table)", c["items_sold"], "=ROWS(Item[ItemID])", 0, COUNT)
    b.check(t, "invoice lines (Analysis!B3)", c["lines"], "=Analysis!B3", 0, COUNT)
    b.check(t, "invoices (Analysis!B4)", c["invoices"], "=Analysis!B4", 0, COUNT)
    b.check(t, "line total (Analysis!B5)", round(c["line_total"], 2), "=Analysis!B5")
    b.check(t, "invoice subtotal (Analysis!B6)", round(c["subtotal"], 2), "=Analysis!B6")
    b.check(t, "difference (Analysis!B7)", 0, "=Analysis!B7")
    b.check(t, "discount taken (Analysis!B8)", round(c["discount"], 2), "=Analysis!B8")
    b.check(t, "list amount (Analysis!B9)", round(c["list_amount"], 2), "=Analysis!B9")


def t4_2(b: Build) -> None:
    wb, e = b.wb, b.exp
    ws = xl.sheet(wb, "Parameters", before=ws_(b, "Analysis"))
    values(ws, {"A1": "Parameter", "B1": "Value", "C1": "Description", "A3": "Threshold percentile", "B3": 0.9,
                "C3": "Share of lines at or below the threshold", "A4": "Large-line threshold",
                "C4": "Line total above which a line counts as large"})
    xl.name_cell(wb, "ThresholdPercentile", "Parameters!$B$3")
    ws.Range("B3").Font.Color = xl.BLUE
    ws.Range("B4").Formula2 = "=PERCENTILE.INC(SalesInvoiceLine[LineTotal],ThresholdPercentile)"
    xl.name_cell(wb, "LargeLineThreshold", "Parameters!$B$4")
    ws.Range("B4").NumberFormat = "$#,##0.00"
    ws.Range("A1:C1").Font.Bold = True
    ws.Columns("A").ColumnWidth = 24
    ws.Columns("B").ColumnWidth = 14
    ws.Columns("C").ColumnWidth = 48

    a = ws_(b, "Analysis")
    values(a, {"A11": "Large lines", "A12": "Share of line total",
               "A14": "Invoice lines by pricing method and discount rate", "A20": "Total", "F15": "Total",
               "A22": "Share of all invoice lines"})
    formulas(a, {"B11": '=COUNTIFS(SalesInvoiceLine[LineTotal],">"&LargeLineThreshold)',
                 "B12": '=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[LineTotal],">"&LargeLineThreshold)/$B$5'})
    a.Range("B12").NumberFormat = "0.0%"
    for j, rate in enumerate(RATES):
        a.Cells(15, 2 + j).Value = rate
    a.Range("B15:E15").NumberFormat = "0%"
    cols = "BCDE"
    for i, method in enumerate(METHODS):
        r = 16 + i
        a.Cells(r, 1).Value = method
        a.Cells(23 + i, 1).Value = method
        for j, col in enumerate(cols):
            a.Range(f"{col}{r}").Formula2 = (f"=COUNTIFS(SalesInvoiceLine[PricingMethod],$A{r},"
                                             f"SalesInvoiceLine[Discount],{col}$15)")
            a.Range(f"{col}{23 + i}").Formula2 = f"={col}{r}/$F$20"
        a.Range(f"F{r}").Formula2 = f"=SUM(B{r}:E{r})"
    for col in "BCDEF":
        a.Range(f"{col}20").Formula2 = f"=SUM({col}16:{col}19)"
    a.Range("B23:E26").NumberFormat = "0.0%"

    b.sheets["Parameters"] = "the analysis parameters"
    b.sheets["Analysis"] = "control totals, the large lines, and the grid of lines by pricing method and discount rate"
    th = e.threshold(0.9)
    t = "4.2"
    b.check(t, "large-line threshold (Parameters!B4)", round(th["threshold"], 2), "=Parameters!B4")
    b.check(t, "large lines (Analysis!B11)", th["large"], "=Analysis!B11", 0, COUNT)
    b.check(t, "their share of the line total (Analysis!B12)", round(th["share"], 6), "=Analysis!B12", 1e-6, PCT)
    b.check(t, "grid grand total equals the invoice lines (Analysis!F20)", e.control["lines"], "=Analysis!F20", 0, COUNT)
    b.check(t, "share block adds up to 100% (Analysis!B23:E26)", 1, "=SUM(Analysis!B23:E26)", 1e-9, PCT)
    b.check(t, "Segment Price List lines with no discount (Analysis!B19)", e.grid[("Segment Price List", 0)],
            "=Analysis!B19", 0, COUNT)
    b.check(t, "Base List lines with a discount (Analysis!C17:E17)", 0, "=SUM(Analysis!C17:E17)", 0, COUNT)


def t4_3(b: Build) -> None:
    wb, e = b.wb, b.exp
    assert e.top_promotion == PROMO, f"promotion {e.top_promotion}, not {PROMO}, has the most invoice lines"
    p = ws_(b, "Parameters")
    v = p.Range("B3").Validation
    v.Delete()
    v.Add(Type=xl.XL_VALIDATE_DECIMAL, AlertStyle=xl.XL_VALID_ALERT_STOP, Operator=xl.XL_BETWEEN,
          Formula1="0.5", Formula2="0.99")
    v.InputTitle = "Threshold percentile"
    v.InputMessage = "Enter a share from 0.5 to 0.99, such as 0.9."
    v.ErrorTitle = "Threshold percentile"
    v.ErrorMessage = "The threshold percentile must be a share from 0.5 to 0.99."
    v.ShowInput = True
    v.ShowError = True

    lines = xl.table(wb, "SalesInvoiceLine")
    ws = ws_(b, "SalesInvoiceLine")
    assert lines.ListColumns("Discount").Range.Column == 10, "Discount is not column J"
    ws.Activate()
    ws.Range("A2").Select()                 # the rule is read relative to the active cell, as in Step 2
    rule = lines.DataBodyRange.FormatConditions.Add(xl.XL_EXPRESSION, 1, "=$J2>0")   # Operator is ignored for a formula rule
    rule.Interior.Color = xl.LIGHT_FILL
    srt = lines.Sort
    srt.SortFields.Clear()
    srt.SortFields.Add(Key=lines.ListColumns("PromotionID").Range, SortOn=0, Order=xl.XL_ASCENDING)
    srt.SortFields.Add(Key=lines.ListColumns("DiscountAmount").Range, SortOn=0, Order=xl.XL_DESCENDING)
    srt.Header = xl.XL_YES
    srt.Apply()
    cache = wb.SlicerCaches.Add2(lines, "PromotionID")
    # Late-bound Slicers.Add ignores its named arguments, so the slicer's name, caption and place are set afterwards.
    # A slicer's place is fixed in points, while the Table grows (Tutorial 5.2 adds six columns) and its columns widen
    # when a refresh autofits them, so it goes well to the right, in column AE (moving it later crashed Excel).
    slicer = xl.retry(cache.Slicers.Add, ws)
    for attr, value in (("Name", "PromotionID"), ("Caption", "PromotionID"), ("Top", 15),
                        ("Left", ws.Cells(1, 31).Left), ("Width", 144), ("Height", 260)):
        xl.retry(lambda a=attr, v=value: setattr(slicer, a, v))
    cache.ClearManualFilter()                # Step 6d: every line in view again

    a = ws_(b, "Analysis")
    values(a, {"A28": "Lines in view", "A29": "Discount in view", "A30": "Discount, all lines"})
    formulas(a, {"B28": "=SUBTOTAL(103,SalesInvoiceLine[SalesInvoiceLineID])",
                 "B29": "=SUBTOTAL(109,SalesInvoiceLine[DiscountAmount])",
                 "B30": "=SUM(SalesInvoiceLine[DiscountAmount])"})
    a.Range("B29:B30").NumberFormat = MONEY

    promo = e.promotion(PROMO)
    start, end = long_date(promo["start"], year=False), long_date(promo["end"])
    b.doc.update({
        "Purpose": f"Diagnose the decline in Furniture gross margin from the third to the fourth quarter of fiscal "
                   f"{b.year}, as requested by the controller.",
        "Source": "CharlesRiver.xlsx (in C:\\CharlesRiver); Tables T16_SalesInvoice, T17_SalesInvoiceLine, T44_Item, "
                  "and T7_PromotionProgram, imported with Power Query.",
        "Query steps": "Item keeps only items with a list price, and eleven columns; SalesInvoice has its date columns "
                       "set to the Date type; FreightAmount and Discount have the decimal number type in their "
                       "Changed Type steps; the other queries keep every row and column.",
        "Parameters": "ThresholdPercentile (Parameters!B3, an input validated between 0.5 and 0.99) and "
                      "LargeLineThreshold (Parameters!B4, a formula).",
        "Calculated columns": "SalesInvoiceLine: ListAmount, ROUND([@Quantity]*[@BaseListPrice],2); DiscountAmount, "
                              "ROUND([@Quantity]*[@UnitPrice]*[@Discount],2).",
        "Conventions": "Blue font marks input cells; black font marks formulas.",
        "Prepared by": "Accounting Analytics companion file",
        "Reviewed by": "",
        "Open questions": f"Promotion {PROMO}, the {promo['name']} ({promo['pct'] * 100:.0f} percent, {start} to {end}), has the most "
                          "promotion lines and the most discount dollars, and its dates straddle the two quarters under "
                          "review. Its effect on Furniture prices in each quarter cannot yet be measured, because the "
                          "invoice lines carry no invoice date or item group."})
    doc = xl.sheet(wb, "Documentation", before=wb.Worksheets(1))
    b.sheets = {"Documentation": "what the workbook is and how it was built", **b.sheets}
    write_documentation(b)
    # Step 9's tab order already holds, because each worksheet was added where it belongs (moving a worksheet that
    # holds a slicer can crash Excel under COM, so the builder never moves one)
    order = [w.Name for w in wb.Worksheets]
    assert order[:7] == ["Documentation", "SalesInvoice", "SalesInvoiceLine", "Item", "PromotionProgram", "Parameters",
                         "Analysis"], order
    doc.Activate()

    t = "4.3"
    b.check(t, "lines in view with the slicer cleared (Analysis!B28)", e.control["lines"], "=Analysis!B28", 0, COUNT)
    b.check(t, "discount in view (Analysis!B29)", round(e.control["discount"], 2), "=Analysis!B29")
    b.check(t, "discount, all lines (Analysis!B30)", round(e.control["discount"], 2), "=Analysis!B30")
    b.check(t, f"promotion {PROMO} lines, the most of any promotion", promo["lines"],
            f"=COUNTIFS(SalesInvoiceLine[PromotionID],{PROMO})", 0, COUNT)
    b.check(t, f"promotion {PROMO} discount dollars", round(promo["discount"], 2),
            f"=SUMIFS(SalesInvoiceLine[DiscountAmount],SalesInvoiceLine[PromotionID],{PROMO})")


# --- Chapter 5 -----------------------------------------------------------------------------------------------------

def t5_1(b: Build) -> None:
    wb, e = b.wb, b.exp
    item = xl.table(wb, "Item")
    xl.add_column(item, "ProductType", "=MID([@ItemCode],5,3)")
    xl.add_column(item, "CodeCheck", '=AND(LEN([@ItemCode])=12,MID([@ItemCode],4,1)="-",MID([@ItemCode],8,1)="-")')
    inv = xl.table(wb, "SalesInvoice")
    xl.add_column(inv, "FiscalYear", "=YEAR([@InvoiceDate])", "0")
    xl.add_column(inv, "FiscalQuarter", "=ROUNDUP(MONTH([@InvoiceDate])/3,0)", "0")
    xl.add_column(inv, "Period", '=[@FiscalYear]&"-Q"&[@FiscalQuarter]')
    xl.add_column(inv, "DaysToDue", "=[@DueDate]-[@InvoiceDate]", "0")
    xl.add_column(inv, "TermsGroup", '=IFS([@DaysToDue]<=30,"Up to 30 days",[@DaysToDue]<=60,"31 to 60 days",'
                                     'TRUE,"Over 60 days")')
    xl.add_column(inv, "StandardTerms", "=OR([@DaysToDue]=30,[@DaysToDue]=45,[@DaysToDue]=60,[@DaysToDue]=90)")
    a = ws_(b, "Analysis")
    values(a, {"A39": "Invoices with nonstandard terms", "A40": "Item codes failing the check"})
    formulas(a, {"B39": "=COUNTIF(SalesInvoice[StandardTerms],FALSE)", "B40": "=COUNTIF(Item[CodeCheck],FALSE)"})
    b.doc["Calculated columns"] += (" Item: ProductType, MID([@ItemCode],5,3); CodeCheck, the item code's form. "
                                    "SalesInvoice: FiscalYear, FiscalQuarter, Period, DaysToDue, TermsGroup (IFS), and "
                                    "StandardTerms (OR).")
    b.sheets["Analysis"] += "; checks in B39 (nonstandard terms) and B40 (item codes)"
    b.sheets["Item"] += " with ProductType and CodeCheck"
    b.sheets["SalesInvoice"] += " with fiscal period and payment-terms columns"
    write_documentation(b)
    terms = e.terms
    t = "5.1"
    b.check(t, "invoices with nonstandard terms (Analysis!B39)", terms["nonstandard"], "=Analysis!B39", 0, COUNT)
    b.check(t, "item codes failing the check (Analysis!B40)", e.code_failures, "=Analysis!B40", 0, COUNT)
    for g in ("Up to 30 days", "31 to 60 days", "Over 60 days"):
        b.check(t, f"invoices with terms {g.lower()}", terms["groups"][g], f'=COUNTIF(SalesInvoice[TermsGroup],"{g}")',
                0, COUNT)
    b.check(t, "distinct Period labels", terms["periods"], "=ROWS(UNIQUE(SalesInvoice[Period]))", 0, COUNT)


def t5_2(b: Build) -> None:
    wb, e = b.wb, b.exp
    xl.add_query(wb, "SalesOrder", nav(b, 9, "SalesOrder", extra=[
        ("Removed Other Columns", pq.select_columns(["SalesOrderID", "OrderNumber", "OrderDate", "CustomerID", "Status"])),
        ("Changed Type1", pq.transform_types([("OrderDate", "type date")]))]))
    xl.load_query(wb, "SalesOrder", "SalesOrder", after=ws_(b, "PromotionProgram"))
    lines = xl.table(wb, "SalesInvoiceLine")
    xl.add_column(lines, "InvoiceDate",
                  '=XLOOKUP([@SalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[InvoiceDate],"No match")',
                  "yyyy-mm-dd")
    xl.add_column(lines, "Period", '=XLOOKUP([@SalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[Period],"No match")')
    xl.add_column(lines, "SalesOrderID",
                  '=XLOOKUP([@SalesInvoiceID],SalesInvoice[SalesInvoiceID],SalesInvoice[SalesOrderID],"No match")', "0")
    xl.add_column(lines, "OrderDate",
                  '=IFERROR(INDEX(SalesOrder[OrderDate],MATCH([@SalesOrderID],SalesOrder[SalesOrderID],0)),"No match")',
                  "yyyy-mm-dd")
    xl.add_column(lines, "ItemGroup", '=XLOOKUP([@ItemID],Item[ItemID],Item[ItemGroup],"No match")')
    xl.add_column(lines, "ProductType", '=XLOOKUP([@ItemID],Item[ItemID],Item[ProductType],"No match")')
    a = ws_(b, "Analysis")
    quarters = [f"{b.year}-Q{k}" for k in range(1, 5)]
    end = e.promotions[PROMO]["end"]
    y, m, d = (int(x) for x in end.split("-"))
    values(a, {"A41": "Lookups not matched", "A43": "Furniture revenue by quarter",
               "A47": f"Promotion {PROMO} lines invoiced after its end date"})
    for col, label in zip("BCDE", quarters):
        a.Range(f"{col}44").NumberFormat = "@"
        a.Range(f"{col}44").Value = label
        a.Range(f"{col}45").Formula2 = (f'=SUMIFS(SalesInvoiceLine[LineTotal],SalesInvoiceLine[ItemGroup],"Furniture",'
                                        f"SalesInvoiceLine[Period],{col}$44)")
    a.Range("B45:E45").NumberFormat = MONEY
    formulas(a, {"B41": '=COUNTIF(SalesInvoiceLine[[InvoiceDate]:[ProductType]],"No match")',
                 "B47": f'=COUNTIFS(SalesInvoiceLine[PromotionID],{PROMO},SalesInvoiceLine[InvoiceDate],'
                        f'">"&DATE({y},{m},{d}))'})
    b.doc["Source"] = b.doc["Source"].replace("and T7_PromotionProgram", "T7_PromotionProgram, and T9_SalesOrder")
    b.doc["Query steps"] += " SalesOrder keeps five columns, with OrderDate set to the Date type."
    b.doc["Calculated columns"] += (" SalesInvoiceLine lookups: InvoiceDate, Period, SalesOrderID (XLOOKUP on "
                                    "SalesInvoice), OrderDate (INDEX and MATCH on SalesOrder, inside IFERROR), ItemGroup "
                                    "and ProductType (XLOOKUP on Item).")
    b.sheets["SalesOrder"] = "the sales orders (query SalesOrder)"
    b.sheets["SalesInvoiceLine"] += " and six lookup columns"
    b.sheets["Analysis"] += "; lookup check (B41), Furniture revenue by quarter (row 45), late promotion lines (B47)"
    write_documentation(b)
    fq = e.group_by_quarter("Furniture", b.year)
    t = "5.2"
    b.check(t, "lookups not matched (Analysis!B41)", 0, "=Analysis!B41", 0, COUNT)
    for col, label in zip("BCDE", quarters):
        b.check(t, f"Furniture revenue {label} (Analysis!{col}45)", round(fq[label], 2), f"=Analysis!{col}45")
    b.check(t, f"promotion {PROMO} lines invoiced after {end} (Analysis!B47)", e.promotion_after_end(PROMO),
            "=Analysis!B47", 0, COUNT)


INVOICE_LINES_STEPS = [
    ("Source", "SalesInvoiceLine"),
    ("Merged Queries", pq.merge("SalesInvoice", "SalesInvoiceID", "SalesInvoiceID", "SalesInvoice")),
    ("Expanded SalesInvoice", pq.expand("SalesInvoice", ["InvoiceDate", "SalesOrderID", "CustomerID"])),
    ("Merged Queries1", pq.merge("Item", "ItemID", "ItemID", "Item")),
    ("Expanded Item", pq.expand("Item", ["ItemCode", "ItemGroup", "StandardCost"])),
    ("Merged Queries2", pq.merge("Customer", "CustomerID", "CustomerID", "Customer")),
    ("Expanded Customer", pq.expand("Customer", ["CustomerSegment", "Region"])),
    ("Added Custom", pq.add_custom("FiscalYear", "Date.Year([InvoiceDate])")),
    ("Added Custom1", pq.add_custom("FiscalQuarter", "Date.QuarterOfYear([InvoiceDate])")),
    ("Added Custom2", pq.add_custom("Period", 'Text.From([FiscalYear]) & "-Q" & Text.From([FiscalQuarter])')),
    ("Added Custom3", pq.add_custom("ProductType", "Text.Middle([ItemCode], 4, 3)")),
    ("Added Custom4", pq.add_custom("WholeQuantity", "[Quantity] = Number.RoundDown([Quantity])")),
    ("Changed Type", pq.transform_types([("FiscalYear", "Int64.Type"), ("FiscalQuarter", "Int64.Type"),
                                         ("Period", "type text"), ("ProductType", "type text"),
                                         ("WholeQuantity", "type logical")])),
]


def t5_3(b: Build) -> None:
    wb, e = b.wb, b.exp
    xl.add_query(wb, "Customer", nav(b, 4, "Customer", extra=[
        ("Removed Other Columns", pq.select_columns(["CustomerID", "CustomerName", "CustomerSegment", "Region"]))]))
    b.queries["InvoiceLines"] = list(INVOICE_LINES_STEPS)
    xl.add_query(wb, "InvoiceLines", pq.steps_query(b.queries["InvoiceLines"]))
    xl.load_query(wb, "InvoiceLines", "InvoiceLines", after=ws_(b, "SalesOrder"))
    xl.load_query(wb, "Customer", "Customer", after=ws_(b, "InvoiceLines"))
    a = ws_(b, "Analysis")
    values(a, {"A49": "InvoiceLines rows", "A50": "InvoiceLines line total", "A52": "Furniture revenue from InvoiceLines",
               "A53": "Lines with a fractional quantity"})
    formulas(a, {"B49": "=COUNTA(InvoiceLines[SalesInvoiceLineID])", "B50": "=SUM(InvoiceLines[LineTotal])",
                 "B53": "=COUNTIF(InvoiceLines[WholeQuantity],FALSE)"})
    for col in "BCDE":
        a.Range(f"{col}52").Formula2 = (f'=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],"Furniture",'
                                        f"InvoiceLines[Period],{col}$44)")
    a.Range("B50").NumberFormat = MONEY
    a.Range("B52:E52").NumberFormat = MONEY
    b.doc["Source"] = b.doc["Source"].replace("and T9_SalesOrder", "T9_SalesOrder, and T4_Customer")
    b.doc["Query steps"] += (" Customer keeps four columns. InvoiceLines is a reference to SalesInvoiceLine with left "
                             "outer merges with SalesInvoice, Item, and Customer, and five custom columns (FiscalYear, "
                             "FiscalQuarter, Period, ProductType, WholeQuantity).")
    b.doc["Open questions"] += (" Most invoice lines carry a fractional quantity, even for items sold by the unit, a "
                                "known limitation of the quantity data.")
    b.sheets["InvoiceLines"] = "the invoice lines with their invoice, item, and customer details (query InvoiceLines)"
    b.sheets["Customer"] = "the customers (query Customer)"
    b.sheets["Analysis"] += "; InvoiceLines checks (rows 49 to 53)"
    write_documentation(b)
    c, fq = e.control, e.group_by_quarter("Furniture", b.year)
    t = "5.3"
    b.check(t, "InvoiceLines rows (Analysis!B49)", c["lines"], "=Analysis!B49", 0, COUNT)
    b.check(t, "InvoiceLines line total (Analysis!B50)", round(c["line_total"], 2), "=Analysis!B50")
    for col, k in zip("BCDE", range(1, 5)):
        label = f"{b.year}-Q{k}"
        b.check(t, f"Furniture revenue {label} from InvoiceLines (Analysis!{col}52)", round(fq[label], 2),
                f"=Analysis!{col}52")
    b.check(t, "lines with a fractional quantity (Analysis!B53)", e.fractional, "=Analysis!B53", 0, COUNT)


# --- Chapter 6 -----------------------------------------------------------------------------------------------------

def t6_1(b: Build) -> None:
    wb, e = b.wb, b.exp
    p = ws_(b, "Parameters")
    values(p, {"A5": "Report year", "B5": b.year, "C5": "Fiscal year shown on the Profile worksheet"})
    p.Range("B5").Font.Color = xl.BLUE
    xl.name_cell(wb, "ReportYear", "Parameters!$B$5")
    ws = xl.sheet(wb, "Profile", after=ws_(b, "Analysis"))
    labels = ["Invoice lines", "Line total", "Average line", "Median line", "Standard deviation", "Smallest line",
              "Largest line", "90th percentile"]
    values(ws, {"A1": "Fiscal year"})
    ws.Range("B1").Formula2 = "=ReportYear"
    for i, label in enumerate(labels, start=2):
        ws.Cells(i, 1).Value = label
    crit = "InvoiceLines[FiscalYear],ReportYear"
    flt = "FILTER(InvoiceLines[LineTotal],InvoiceLines[FiscalYear]=ReportYear)"
    formulas(ws, {"B2": f"=COUNTIFS({crit})", "B3": f"=SUMIFS(InvoiceLines[LineTotal],{crit})",
                  "B4": f"=AVERAGEIFS(InvoiceLines[LineTotal],{crit})", "B5": f"=MEDIAN({flt})",
                  "B6": f"=STDEV.S({flt})", "B7": f"=MINIFS(InvoiceLines[LineTotal],{crit})",
                  "B8": f"=MAXIFS(InvoiceLines[LineTotal],{crit})",
                  "B9": f"=PERCENTILE.INC({flt},ThresholdPercentile)"})
    ws.Range("B3:B9").NumberFormat = MONEY
    values(ws, {"A11": "Item group", "B11": "Lines", "C11": "Revenue", "D11": "Average line"})
    for i, g in enumerate(GROUPS):
        r = 12 + i
        ws.Cells(r, 1).Value = g
        formulas(ws, {f"B{r}": f"=COUNTIFS(InvoiceLines[ItemGroup],$A{r},{crit})",
                      f"C{r}": f"=SUMIFS(InvoiceLines[LineTotal],InvoiceLines[ItemGroup],$A{r},{crit})",
                      f"D{r}": f"=C{r}/B{r}"})
    values(ws, {"A17": "Total of groups", "A18": "Difference from control total"})
    formulas(ws, {"B17": "=SUM(B12:B16)", "C17": "=SUM(C12:C16)", "B18": "=B17-B2", "C18": "=C17-B3"})
    ws.Range("C12:D18").NumberFormat = MONEY
    values(ws, {"F1": "From", "G1": "Lines", "F18": "Total"})
    for i in range(16):
        r = 2 + i
        ws.Cells(r, 6).Value = 1000 * i
        if i < 15:
            ws.Range(f"G{r}").Formula2 = (f'=COUNTIFS({crit},InvoiceLines[LineTotal],">="&F{r},'
                                          f'InvoiceLines[LineTotal],"<"&F{r + 1})')
    ws.Range("G17").Formula2 = f'=COUNTIFS({crit},InvoiceLines[LineTotal],">="&F17)'
    ws.Range("G18").Formula2 = "=SUM(G2:G17)"
    ws.Columns("A").ColumnWidth = 28
    ws.Columns("B:D").ColumnWidth = 15
    shape = ws.Shapes.AddChart2(-1, xl.XL_COLUMN_CLUSTERED, ws.Range("I2").Left, ws.Range("I2").Top, 480, 288)
    chart = shape.Chart
    chart.SetSourceData(ws.Range("G1:G17"))
    chart.SeriesCollection(1).XValues = ws.Range("F2:F17")
    chart.ChartGroups(1).GapWidth = 0
    b.doc["Parameters"] += " ReportYear (Parameters!B5, an input)."
    b.sheets["Profile"] = "the profile of the report year's invoice lines, revenue by item group, and a histogram"
    write_documentation(b)
    pr = e.profile(b.year)
    t = "6.1"
    for addr, key, fmt, tol in (("B2", "count", COUNT, 0), ("B3", "total", MONEY, 0.005), ("B4", "average", MONEY, 1e-6),
                                ("B5", "median", MONEY, 1e-6), ("B6", "stdev", MONEY, 1e-6), ("B7", "smallest", MONEY, 1e-6),
                                ("B8", "largest", MONEY, 1e-6), ("B9", "p90", MONEY, 1e-6)):
        value = pr[key] if tol != 0.005 else round(pr[key], 2)
        b.check(t, f"{labels[int(addr[1:]) - 2].lower()} (Profile!{addr})", value, f"=Profile!{addr}", tol, fmt)
    for i, g in enumerate(GROUPS):
        b.check(t, f"{g} revenue (Profile!C{12 + i})", round(pr["groups"][g]["revenue"], 2), f"=Profile!C{12 + i}")
    b.check(t, "difference in lines (Profile!B18)", 0, "=Profile!B18", 0, COUNT)
    b.check(t, "difference in revenue (Profile!C18)", 0, "=Profile!C18")
    b.check(t, "first bin, under 1,000 (Profile!G2)", pr["bins"][0], "=Profile!G2", 0, COUNT)
    b.check(t, "last bin, 15,000 or more (Profile!G17)", pr["bins"][-1], "=Profile!G17", 0, COUNT)
    b.check(t, "bins add up to the year's lines (Profile!G18)", pr["count"], "=Profile!G18", 0, COUNT)


def t6_2(b: Build) -> None:
    wb, e = b.wb, b.exp
    steps = b.queries["InvoiceLines"]
    steps += [("Added Custom5", pq.add_custom("StdCostAmount", "[Quantity] * [StandardCost]")),
              ("Changed Type1", pq.transform_types([("StdCostAmount", "type number")]))]
    xl.wait_ready(wb.Application)
    xl.retry(lambda: setattr(wb.Queries("InvoiceLines"), "Formula", pq.steps_query(steps)))
    xl.wait_ready(wb.Application)
    xl.table(wb, "InvoiceLines").QueryTable.Refresh(False)

    cache = wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData="InvoiceLines")
    rev = xl.sheet(wb, "RevenuePivot", after=ws_(b, "Profile"))
    pt = cache.CreatePivotTable(TableDestination=rev.Range("A3"), TableName="PivotTable1")
    pt.PivotFields("FiscalYear").Orientation = xl.XL_PAGE
    pt.PivotFields("Period").Orientation = xl.XL_COLUMN
    pt.PivotFields("ItemGroup").Orientation = xl.XL_ROW
    lt = pt.AddDataField(pt.PivotFields("LineTotal"), "Sum of LineTotal", xl.XL_SUM)
    lt.NumberFormat = MONEY
    pt.PivotFields("FiscalYear").CurrentPage = str(b.year)
    pt.CalculatedFields().Add("MarginPct", "=(LineTotal-StdCostAmount)/LineTotal", True)
    mp = pt.AddDataField(pt.PivotFields("MarginPct"), "Sum of MarginPct", xl.XL_SUM)
    mp.NumberFormat = PCT
    pt.DataPivotField.Orientation = xl.XL_ROW
    pt.DataPivotField.Position = 2

    seg = xl.sheet(wb, "SegmentPivot", after=rev)
    ps = cache.CreatePivotTable(TableDestination=seg.Range("A3"), TableName="PivotTable2")
    ps.PivotFields("CustomerSegment").Orientation = xl.XL_ROW
    ps.PivotFields("FiscalYear").Orientation = xl.XL_COLUMN
    s1 = ps.AddDataField(ps.PivotFields("LineTotal"), "Sum of LineTotal", xl.XL_SUM)
    s2 = ps.AddDataField(ps.PivotFields("LineTotal"), "Change from previous year", xl.XL_SUM)
    for item in ps.PivotFields("FiscalYear").PivotItems():
        if int(float(item.Name)) < b.year - 1:
            item.Visible = False
    s2.Calculation = xl.XL_PERCENT_DIFFERENCE_FROM
    s2.BaseField = "FiscalYear"
    s2.BaseItem = "(previous)"
    s2.NumberFormat = PCT
    s1.NumberFormat = MONEY

    mc = xl.sheet(wb, "MarginChart", after=seg)
    pm = cache.CreatePivotTable(TableDestination=mc.Range("A3"), TableName="PivotTable3")
    pm.PivotFields("FiscalYear").Orientation = xl.XL_PAGE
    pm.PivotFields("Period").Orientation = xl.XL_ROW
    pm.PivotFields("ItemGroup").Orientation = xl.XL_COLUMN
    m = pm.AddDataField(pm.PivotFields("MarginPct"), "Sum of MarginPct", xl.XL_SUM)
    m.NumberFormat = PCT
    pm.PivotFields("FiscalYear").CurrentPage = str(b.year)
    pm.PivotFields("ItemGroup").PivotItems("Services").Visible = False
    shape = mc.Shapes.AddChart2(-1, xl.XL_LINE_MARKERS, mc.Range("H3").Left, mc.Range("H3").Top, 480, 288)
    shape.Chart.SetSourceData(pm.TableRange1)

    b.doc["Query steps"] += " InvoiceLines adds StdCostAmount, Quantity times StandardCost, as a decimal number."
    b.extra.append(["Calculated fields", "MarginPct, (LineTotal-StdCostAmount)/LineTotal, shared by the PivotTables."])
    b.sheets.update(RevenuePivot=f"revenue and margin at standard cost by item group and quarter, fiscal {b.year}",
                    SegmentPivot=f"revenue by customer segment, {b.year - 1} and {b.year}, with the change",
                    MarginChart=f"a PivotChart of the margins by quarter, fiscal {b.year}, without Services")
    write_documentation(b)
    pr, mg = e.profile(b.year), e.margins(b.year)
    t = "6.2"
    gp = "GETPIVOTDATA"
    b.check(t, "RevenuePivot grand total equals the Profile control total", round(pr["total"], 2),
            f'={gp}("Sum of LineTotal",RevenuePivot!$A$3)')
    for q in (3, 4):
        period = f"{b.year}-Q{q}"
        b.check(t, f"Furniture margin at standard cost, {period}", round(mg[("Furniture", period)], 6),
                f'={gp}("Sum of MarginPct",RevenuePivot!$A$3,"ItemGroup","Furniture","Period","{period}")', 1e-6, PCT)
    b.check(t, f"Services margin, {b.year}-Q4 (no standard cost)", 1,
            f'={gp}("Sum of MarginPct",RevenuePivot!$A$3,"ItemGroup","Services","Period","{b.year}-Q4")', 1e-9, PCT)
    b.check(t, f"Wholesale revenue, {b.year} (SegmentPivot)", round(e.segment_revenue("Wholesale", b.year), 2),
            f'={gp}("Sum of LineTotal",SegmentPivot!$A$3,"CustomerSegment","Wholesale","FiscalYear",{b.year})')


def first_cache(b: Build):
    """The pivot cache of the InvoiceLines PivotTables, which share their calculated fields (Tutorial 6.3, Step 3)."""
    return ws_(b, "RevenuePivot").PivotTables("PivotTable1").PivotCache()


def only_items(field, keep: list[str]) -> None:
    for item in field.PivotItems():
        if item.Name not in keep:
            item.Visible = False


def t6_3(b: Build) -> None:
    wb, e = b.wb, b.exp
    y = b.year
    q3, q4 = f"{y}-Q3", f"{y}-Q4"
    steps = b.queries["InvoiceLines"]
    steps += [("Added Custom6", pq.add_custom("ListAmount", "[Quantity] * [BaseListPrice]")),
              ("Added Custom7", pq.add_custom("DiscountAmount", "[Quantity] * [UnitPrice] * [Discount]")),
              ("Changed Type2", pq.transform_types([("ListAmount", "type number"), ("DiscountAmount", "type number")]))]
    xl.wait_ready(wb.Application)
    xl.retry(lambda: setattr(wb.Queries("InvoiceLines"), "Formula", pq.steps_query(steps)))
    xl.wait_ready(wb.Application)
    xl.refresh_all(wb)                                       # Step 1c: Close & Load, then Refresh All
    cache = first_cache(b)

    drv = xl.sheet(wb, "Drivers", after=ws_(b, "MarginChart"))
    pt = cache.CreatePivotTable(TableDestination=drv.Range("A3"), TableName="PivotTable4")
    pt.PivotFields("ItemGroup").Orientation = xl.XL_PAGE
    pt.PivotFields("ItemGroup").CurrentPage = "Furniture"
    pt.PivotFields("Period").Orientation = xl.XL_COLUMN
    only_items(pt.PivotFields("Period"), [q3, q4])
    for f in ("Quantity", "ListAmount", "LineTotal", "DiscountAmount", "StdCostAmount"):
        pt.AddDataField(pt.PivotFields(f), f"Sum of {f}", xl.XL_SUM).NumberFormat = MONEY
    pt.DataPivotField.Orientation = xl.XL_ROW
    pt.ColumnGrand = False
    pt.RowGrand = False
    pt.AddDataField(pt.PivotFields("MarginPct"), "Sum of MarginPct", xl.XL_SUM).NumberFormat = PCT
    calc = {"PricePerUnit": "=LineTotal/Quantity", "ListPerUnit": "=ListAmount/Quantity",
            "CostPerUnit": "=StdCostAmount/Quantity",
            "MarginBeforeDiscountPct": "=(LineTotal+DiscountAmount-StdCostAmount)/(LineTotal+DiscountAmount)"}
    for name, formula in calc.items():
        pt.CalculatedFields().Add(name, formula, True)
        fld = pt.AddDataField(pt.PivotFields(name), f"Sum of {name}", xl.XL_SUM)
        fld.NumberFormat = PCT if name.endswith("Pct") else MONEY

    br = xl.sheet(wb, "Bridge", after=drv)
    values(br, {"A3": "Driver", "A9": "Margin"})
    for col, period in (("B", q3), ("C", q4)):
        br.Range(f"{col}3").NumberFormat = "@"
        br.Range(f"{col}3").Value = period
    for r, f in enumerate(("Quantity", "ListAmount", "LineTotal", "DiscountAmount", "StdCostAmount"), start=4):
        br.Cells(r, 1).Value = f
        for col, period in (("B", q3), ("C", q4)):
            br.Range(f"{col}{r}").Formula = f'=GETPIVOTDATA("Sum of {f}",Drivers!$A$3,"Period","{period}")'
    formulas(br, {"B9": "=B6-B8", "C9": "=C6-C8"})
    labels = ["Margin per unit", "List margin per unit", "Price-list reduction per unit", "Discount per unit"]
    per_unit = ["=B9/B4", "=(B5-B8)/B4", "=(B5-B6-B7)/B4", "=B7/B4"]
    for i, (label, f) in enumerate(zip(labels, per_unit)):
        br.Cells(11 + i, 1).Value = label
        br.Range(f"B{11 + i}").Formula = f
        br.Range(f"C{11 + i}").Formula = f.replace("B", "C")
    bridge_labels = [f"{q3} margin", "Volume", "Mix", "Price lists", "Promotions", "Cost", f"{q4} margin", "Check"]
    bridge = ["=B9", "=(C4-B4)*B11", "=C4*(C12-B12)", "=-C4*(C13-B13)", "=-C4*(C14-B14)", 0, "=C9",
              "=B16+SUM(B17:B21)-B22"]
    for i, (label, f) in enumerate(zip(bridge_labels, bridge)):
        br.Cells(16 + i, 1).Value = label
        br.Range(f"B{16 + i}").Formula = f
    br.Range("C21").Value = "Each item has one standard cost"
    br.Range("B4:C14").NumberFormat = MONEY
    br.Range("B16:B23").NumberFormat = "#,##0"
    br.Columns("A").ColumnWidth = 30
    br.Columns("B:C").ColumnWidth = 16
    shape = br.Shapes.AddChart2(-1, xl.XL_WATERFALL, br.Range("E3").Left, br.Range("E3").Top, 480, 300)
    chart = shape.Chart
    chart.SetSourceData(br.Range("A16:B22"))
    series = chart.FullSeriesCollection(1)
    series.Points(1).IsTotal = True
    series.Points(7).IsTotal = True
    chart.Axes(2).MinimumScale = 1600000
    chart.HasTitle = True
    chart.ChartTitle.Text = f"Furniture margin, {q3} to {q4} (the axis starts at 1.6 million)"

    dis = xl.sheet(wb, "Discounts", after=br)
    pd_ = cache.CreatePivotTable(TableDestination=dis.Range("A3"), TableName="PivotTable5")
    pd_.PivotFields("ItemGroup").Orientation = xl.XL_PAGE
    pd_.PivotFields("ItemGroup").CurrentPage = "Furniture"
    pd_.PivotFields("Period").Orientation = xl.XL_COLUMN
    only_items(pd_.PivotFields("Period"), [q3, q4])
    pd_.PivotFields("PromotionID").Orientation = xl.XL_ROW
    pd_.AddDataField(pd_.PivotFields("SalesInvoiceLineID"), "Count of Lines", xl.XL_COUNT)
    pd_.AddDataField(pd_.PivotFields("DiscountAmount"), "Sum of Discount", xl.XL_SUM).NumberFormat = MONEY
    pd_.ColumnGrand = False
    pd_.RowGrand = False

    bg = expected.bridge(e, y)
    b.doc["Query steps"] += " InvoiceLines also adds ListAmount and DiscountAmount, unrounded, as decimal numbers."
    b.extra[0][1] += (" PricePerUnit, ListPerUnit, CostPerUnit, and MarginBeforeDiscountPct, "
                      "(LineTotal+DiscountAmount-StdCostAmount)/(LineTotal+DiscountAmount).")
    b.sheets.update(Drivers=f"the Furniture drivers of {q3} and {q4} (PivotTable)",
                    Bridge="the Furniture margin bridge and its waterfall chart",
                    Discounts=f"Furniture discounts by promotion, {q3} and {q4} (PivotTable)")
    b.doc["Open questions"] = ("Most invoice lines carry a fractional quantity, even for items sold by the unit, a known "
                               "limitation of the quantity data.")
    promo = e.promotion(PROMO)
    b.extra.append(["Finding", f"The Furniture margin at standard cost fell from {bg['q3']:,.0f} in {q3} to "
                    f"{bg['q4']:,.0f} in {q4}. The promotions effect, {bg['promotions']:,.0f}, is larger than the whole "
                    f"decline: promotional discounts more than doubled, mostly under promotion {PROMO}, the "
                    f"{promo['name']}, whose orders were invoiced across the end of the third quarter. Volume "
                    f"({bg['volume']:+,.0f}), mix ({bg['mix']:+,.0f}), and price lists ({bg['price']:+,.0f}) were small, "
                    "and standard costs did not change."])
    write_documentation(b)

    t = "6.3"
    b.check(t, "bridge check (Bridge!B23)", 0, "=Bridge!B23", 0.01)
    for addr, key, label in (("B16", "q3", f"{q3} margin"), ("B17", "volume", "volume effect"),
                             ("B18", "mix", "mix effect"), ("B19", "price", "price-list effect"),
                             ("B20", "promotions", "promotions effect"), ("B22", "q4", f"{q4} margin")):
        b.check(t, f"{label} (Bridge!{addr})", round(bg[key], 2), f"=Bridge!{addr}", 0.01)
    for period, key in ((q3, "mbd3"), (q4, "mbd4")):
        b.check(t, f"Furniture margin before discounts, {period}", round(bg[key], 6),
                f'=GETPIVOTDATA("Sum of MarginBeforeDiscountPct",Drivers!$A$3,"Period","{period}")', 1e-6, PCT)
    disc = expected.discounts_by_promotion(e, y)
    for pid, period in ((PROMO, q3), (PROMO, q4), (9, q4)):
        b.check(t, f"Furniture discount of promotion {pid}, {period}", round(disc[(pid, period)][1], 2),
                f'=GETPIVOTDATA("Sum of Discount",Discounts!$A$3,"PromotionID",{pid},"Period","{period}")', 0.01)


# --- Chapter 7 -----------------------------------------------------------------------------------------------------

def freeze(rng) -> None:
    """Replace formulas by their values, as an add-in's output is."""
    rng.Value = rng.Value


def correlation_output(ws, top: str, data: str, labels: list[str]) -> None:
    """The Correlation tool's output: a lower-triangular matrix, written with CORREL and frozen as values."""
    r0, c0 = ws.Range(top).Row, ws.Range(top).Column
    cols = [ws.Range(data).Columns(i + 1) for i in range(3)]
    for i, name in enumerate(labels):
        ws.Cells(r0, c0 + 1 + i).Value = name
        ws.Cells(r0 + 1 + i, c0).Value = name
        for j in range(i + 1):
            cell = ws.Cells(r0 + 1 + i, c0 + 1 + j)
            if i == j:
                cell.Value = 1
            else:
                cell.Formula = f"=CORREL({cols[i].Address},{cols[j].Address})"
    freeze(ws.Range(ws.Cells(r0, c0), ws.Cells(r0 + 3, c0 + 3)))


def regression_output(wb, sheet_name: str, after, y: str, x: str, x_name: str, y_name: str) -> object:
    """The Regression tool's SUMMARY OUTPUT and RESIDUAL OUTPUT in its layout, computed with LINEST and frozen."""
    ws = xl.sheet(wb, sheet_name, after=after)
    lin = f"LINEST({y},{x},TRUE,TRUE)"
    n = f"COUNT({y})"
    cells = {
        "A1": "SUMMARY OUTPUT", "A3": "Regression Statistics", "A4": "Multiple R", "B4": f"=SQRT(INDEX({lin},3,1))",
        "A5": "R Square", "B5": f"=INDEX({lin},3,1)", "A6": "Adjusted R Square",
        "B6": f"=1-(1-INDEX({lin},3,1))*({n}-1)/({n}-2)", "A7": "Standard Error", "B7": f"=INDEX({lin},3,2)",
        "A8": "Observations", "B8": f"={n}", "A10": "ANOVA", "B11": "df", "C11": "SS", "D11": "MS", "E11": "F",
        "F11": "Significance F", "A12": "Regression", "B12": 1, "C12": f"=INDEX({lin},5,1)", "D12": "=C12/B12",
        "E12": "=D12/D13", "F12": "=F.DIST.RT(E12,B12,B13)", "A13": "Residual", "B13": f"=INDEX({lin},4,2)",
        "C13": f"=INDEX({lin},5,2)", "D13": "=C13/B13", "A14": "Total", "B14": "=B12+B13", "C14": "=C12+C13",
        "B16": "Coefficients", "C16": "Standard Error", "D16": "t Stat", "E16": "P-value", "F16": "Lower 95%",
        "G16": "Upper 95%", "H16": "Lower 95.0%", "I16": "Upper 95.0%", "A17": "Intercept",
        "B17": f"=INDEX({lin},1,2)", "C17": f"=INDEX({lin},2,2)", "A18": x_name, "B18": f"=INDEX({lin},1,1)",
        "C18": f"=INDEX({lin},2,1)", "A22": "RESIDUAL OUTPUT", "A24": "Observation", "B24": f"Predicted {y_name}",
        "C24": "Residuals"}
    for addr, v in cells.items():
        if isinstance(v, str) and v.startswith("="):
            ws.Range(addr).Formula2 = v
        else:
            ws.Range(addr).Value = v
    for r in (17, 18):
        formulas(ws, {f"D{r}": f"=B{r}/C{r}", f"E{r}": f"=T.DIST.2T(ABS(D{r}),$B$13)",
                      f"F{r}": f"=B{r}-T.INV.2T(0.05,$B$13)*C{r}", f"G{r}": f"=B{r}+T.INV.2T(0.05,$B$13)*C{r}",
                      f"H{r}": f"=F{r}", f"I{r}": f"=G{r}"})
    ys, xs = wb.Application.Range(y), wb.Application.Range(x)
    count = ys.Rows.Count
    for i in range(count):
        r = 25 + i
        ws.Cells(r, 1).Value = i + 1
        ws.Cells(r, 2).Formula = f"=$B$17+$B$18*{xs.Cells(i + 1, 1).GetAddress(True, True, 1, True)}"
        ws.Cells(r, 3).Formula = f"={ys.Cells(i + 1, 1).GetAddress(True, True, 1, True)}-B{r}"
    wb.Application.Calculate()
    freeze(ws.Range(f"A1:I{24 + count}"))
    plot = ws.Shapes.AddChart2(-1, xl.XL_XY_SCATTER, ws.Range("K1").Left, ws.Range("K1").Top, 360, 216).Chart
    plot.SetSourceData(ws.Range(f"C25:C{24 + count}"))
    plot.FullSeriesCollection(1).XValues = xs
    plot.HasTitle = True
    plot.ChartTitle.Text = f"{x_name} Residual Plot"
    ws.Columns("A:I").AutoFit()
    return ws


def t7_1(b: Build) -> None:
    wb, e = b.wb, b.exp
    first = b.year - 2
    ws = xl.sheet(wb, "Forecast", after=ws_(b, "Discounts"))
    values(ws, {"A1": "Month", "B1": "MonthIndex", "C1": "Revenue", "D1": "Customers", "E1": "AverageLine",
                "A38": "Control total", "B2": 1})
    ws.Range("A2").Formula = f"{first}-01-01"
    for r in range(3, 38):
        formulas(ws, {f"A{r}": f"=EDATE(A{r - 1},1)", f"B{r}": f"=B{r - 1}+1"})
    for r in range(2, 38):
        month = f'InvoiceLines[InvoiceDate],">="&A{r},InvoiceLines[InvoiceDate],"<"&EDATE(A{r},1)'
        formulas(ws, {
            f"C{r}": f"=SUMIFS(InvoiceLines[LineTotal],{month})",
            f"D{r}": (f"=COUNTA(UNIQUE(FILTER(InvoiceLines[CustomerID],(InvoiceLines[InvoiceDate]>=A{r})*"
                      f"(InvoiceLines[InvoiceDate]<EDATE(A{r},1)))))"),
            f"E{r}": f"=AVERAGEIFS(InvoiceLines[LineTotal],{month})"})
    ws.Range("C38").Formula2 = "=SUM(C2:C37)-SUM(InvoiceLines[LineTotal])"
    ws.Range("A2:A37").NumberFormat = "mmm yyyy"
    ws.Range("C2:C38").NumberFormat = MONEY
    ws.Range("E2:E37").NumberFormat = MONEY
    chart = ws.Shapes.AddChart2(-1, xl.XL_LINE_MARKERS, ws.Range("L1").Left, ws.Range("L1").Top, 480, 288).Chart
    chart.SetSourceData(ws.Range("A1:A37,C1:C37"))
    wb.Application.Calculate()
    # The labeled run's input range includes the header row; CORREL ignores the text, as the tool reads it as labels.
    correlation_output(ws, "G1", "$C$1:$E$37", ["Revenue", "Customers", "AverageLine"])
    correlation_output(ws, "G7", "$C$3:$E$37", ["Column 1", "Column 2", "Column 3"])
    t36 = regression_output(wb, "Trend36", ws, "Forecast!$C$2:$C$37", "Forecast!$B$2:$B$37", "MonthIndex", "Revenue")
    regression_output(wb, "Trend35", t36, "Forecast!$C$3:$C$37", "Forecast!$B$3:$B$37", "X Variable 1", "Y")

    months = [f"{m} {b.year}" for m in ("Oct", "Nov", "Dec")]
    values(ws, {"A40": "Method", "B40": months[0], "C40": months[1], "D40": months[2], "E40": "Quarter",
                "F40": "Error", "G40": "Monthly error", "A41": "Actual", "A42": "Trend", "A43": "Mean",
                "A44": "Same quarter last year", "A47": f"Forecast, {b.year + 1} Q1", "A48": "Low", "A49": "High"})
    for col, r in zip("BCD", (35, 36, 37)):
        formulas(ws, {f"{col}41": f"=C{r}", f"{col}42": f"=FORECAST.LINEAR($B{r},$C$3:$C$34,$B$3:$B$34)",
                      f"{col}43": "=AVERAGE($C$3:$C$34)", f"{col}44": f"=C{r - 12}"})
    for r in range(41, 45):
        ws.Range(f"E{r}").Formula = f"=SUM(B{r}:D{r})"
    for r in range(42, 45):
        formulas(ws, {f"F{r}": f"=E{r}/$E$41-1", f"G{r}": f"=AVERAGE(ABS(B{r}:D{r}-$B$41:$D$41)/$B$41:$D$41)"})
    formulas(ws, {"B47": "=3*AVERAGE(C3:C37)", "B48": "=B47*(1-G43)", "B49": "=B47*(1+G43)"})
    ws.Range("B41:E44").NumberFormat = MONEY
    ws.Range("F42:G44").NumberFormat = PCT
    ws.Range("B47:B49").NumberFormat = MONEY
    ws.Columns("A").ColumnWidth = 24

    series = expected.monthly_series(e, first)
    bt = expected.backtest(series)
    rev = [r["revenue"] for r in series]
    b.sheets.update(Forecast="the monthly revenue series, the correlations, the backtest, and the forecast",
                    Trend36="the regression of revenue on the month, all 36 months (Analysis ToolPak)",
                    Trend35="the same regression without the start-up month (Analysis ToolPak)")
    fc = bt["forecast"]
    b.extra.append(["Forecast", f"Mean method: the average monthly revenue of February {first} to December {b.year}, "
                    f"times three, for {b.year + 1} Q1: {fc['value']:,.0f} (low {fc['low']:,.0f}, high {fc['high']:,.0f}). "
                    f"January {first}, the start-up month, is excluded because it is a start-up month, not a level the "
                    f"business returns to. In the backtest on {b.year} Q4, the mean missed the quarter by "
                    f"{bt['mean']['error']:+.2%} with a monthly error of {bt['mean']['monthly']:.2%}, against "
                    f"{bt['trend']['error']:+.2%} for the trend and {bt['last']['error']:+.2%} (monthly "
                    f"{bt['last']['monthly']:.2%}) for the same quarter last year. The range is the mean's monthly error."])
    write_documentation(b)

    t = "7.1"
    b.check(t, "control total of the monthly series (Forecast!C38)", 0, "=Forecast!C38", 0.01)
    cust = [r["customers"] for r in series]
    avg = [r["average"] for r in series]
    for addr, xs, ys, label in (("H3", rev, cust, "revenue and customers, 36 months"),
                                ("H4", rev, avg, "revenue and average line, 36 months"),
                                ("H9", rev[1:], cust[1:], "revenue and customers, without the start-up month"),
                                ("H10", rev[1:], avg[1:], "revenue and average line, without the start-up month")):
        b.check(t, f"correlation of {label} (Forecast!{addr})", round(expected.correl(xs, ys), 9), f"=Forecast!{addr}",
                1e-9, RATIO)
    r36 = expected.regression([r["index"] for r in series], rev)
    r35 = expected.regression([r["index"] for r in series[1:]], rev[1:])
    for sheet, reg in (("Trend36", r36), ("Trend35", r35)):
        b.check(t, f"R Square ({sheet}!B5)", round(reg["r2"], 9), f"={sheet}!B5", 1e-9, RATIO)
        b.check(t, f"slope ({sheet}!B18)", round(reg["slope"], 6), f"={sheet}!B18", 1e-6)
        b.check(t, f"slope P-value ({sheet}!E18)", round(reg["p"], 9), f"={sheet}!E18", 1e-9, RATIO)
    for r, key in ((42, "trend"), (43, "mean"), (44, "last")):
        b.check(t, f"{key} forecast, error of the quarter (Forecast!F{r})", round(bt[key]["error"], 9),
                f"=Forecast!F{r}", 1e-9, PCT)
        b.check(t, f"{key} forecast, monthly error (Forecast!G{r})", round(bt[key]["monthly"], 9), f"=Forecast!G{r}",
                1e-9, PCT)
    b.check(t, f"forecast of {b.year + 1} Q1 (Forecast!B47)", round(fc["value"], 2), "=Forecast!B47", 0.01)


def t7_2(b: Build) -> None:
    wb, e = b.wb, b.exp
    y = b.year
    close = YEAR_END_CLOSE.format(year=y)
    xl.add_query(wb, "Account", nav(b, 1, "Account", extra=[
        ("Removed Other Columns", pq.select_columns(["AccountID", "AccountNumber", "AccountName"]))]))
    xl.add_query(wb, "BudgetLine", nav(b, 77, "BudgetLine", extra=[
        ("Filtered Rows", pq.select_rows(f"([FiscalYear] = {y})")),
        ("Filtered Rows1", pq.select_rows('([BudgetCategory] <> "Balance Sheet")')),
        ("Merged Queries", pq.merge("Item", "ItemID", "ItemID", "Item")),
        ("Expanded Item", pq.expand("Item", ["ItemGroup"])),
        ("Merged Queries1", pq.merge("Account", "AccountID", "AccountID", "Account")),
        ("Expanded Account", pq.expand("Account", ["AccountNumber", "AccountName"]))]))
    xl.load_query(wb, "BudgetLine", "BudgetLine", after=ws_(b, "Customer"))
    xl.load_query(wb, "Account", "Account", after=ws_(b, "BudgetLine"))
    xl.add_query(wb, "PlannedPrices", pq.steps_query([
        ("Source", "BudgetLine"),
        ("Filtered Rows", pq.select_rows('([BudgetCategory] = "Revenue")')),
        ("Removed Other Columns", pq.select_columns(["FiscalYear", "Month", "ItemID", "UnitAmount"])),
        ("Renamed Columns", pq.rename([("UnitAmount", "PlannedPrice")]))]))     # Enable Load cleared: not loaded
    xl.add_query(wb, "FlexLines", pq.steps_query([
        ("Source", "InvoiceLines"),
        ("Filtered Rows", pq.select_rows(f"([FiscalYear] = {y})")),
        ("Filtered Rows1", pq.select_rows('([ItemGroup] <> "Services")')),
        ("Added Custom", pq.add_custom("Month", "Date.Month([InvoiceDate])")),
        ("Changed Type", pq.transform_types([("Month", "Int64.Type")])),
        ("Merged Queries", pq.merge_keys("PlannedPrices", ["FiscalYear", "Month", "ItemID"], "PlannedPrices")),
        ("Expanded PlannedPrices", pq.expand("PlannedPrices", ["PlannedPrice"])),
        ("Added Custom1", pq.add_custom("FlexRevenue",
                                        "if [PlannedPrice] = null then [LineTotal] else [Quantity] * [PlannedPrice]")),
        ("Changed Type1", pq.transform_types([("PlannedPrice", "type number"), ("FlexRevenue", "type number")]))]))
    xl.load_query(wb, "FlexLines", "FlexLines", after=ws_(b, "Account"))

    rep = xl.sheet(wb, "BudgetReport", after=ws_(b, "Trend35"))
    groups = ["Furniture", "Lighting", "Textiles", "Accessories"]
    for col, g in zip("BCDEF", groups + ["Total"]):
        rep.Range(f"{col}3").Value = g
    labels = ["Static budget revenue", "Static budget COGS", "Static budget margin", "Flexible budget revenue",
              "Flexible budget COGS", "Flexible budget margin", "Actual revenue", "Actual COGS at standard",
              "Actual margin", "Sales-volume variance", "Flexible-budget variance", "Promotional discounts",
              "Price gap before discounts", "Budgeted units", "Actual units"]
    for i, label in enumerate(labels):
        rep.Cells(4 + i, 1).Value = label
    for col in "BCDE":
        g = f"{col}$3"
        formulas(rep, {
            f"{col}4": f'=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[ItemGroup],{g},BudgetLine[BudgetCategory],"Revenue")',
            f"{col}5": f'=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[ItemGroup],{g},BudgetLine[BudgetCategory],"COGS")',
            f"{col}6": f"={col}4-{col}5",
            f"{col}7": f"=SUMIFS(FlexLines[FlexRevenue],FlexLines[ItemGroup],{g})",
            f"{col}8": f"=SUMIFS(FlexLines[StdCostAmount],FlexLines[ItemGroup],{g})",
            f"{col}9": f"={col}7-{col}8",
            f"{col}10": f"=SUMIFS(FlexLines[LineTotal],FlexLines[ItemGroup],{g})",
            f"{col}11": f"={col}8",
            f"{col}12": f"={col}10-{col}11",
            f"{col}13": f"={col}9-{col}6",
            f"{col}14": f"={col}12-{col}9",
            f"{col}15": f"=SUMIFS(FlexLines[DiscountAmount],FlexLines[ItemGroup],{g})",
            f"{col}16": f"={col}14+{col}15",
            f"{col}17": f'=SUMIFS(BudgetLine[Quantity],BudgetLine[ItemGroup],{g},BudgetLine[BudgetCategory],"Revenue")',
            f"{col}18": f"=SUMIFS(FlexLines[Quantity],FlexLines[ItemGroup],{g})"})
    for r in list(range(4, 17)) + [17, 18]:
        rep.Range(f"F{r}").Formula = f"=SUM(B{r}:E{r})"
    values(rep, {"A20": "Lines without a planned price"})
    rep.Range("B20").Formula2 = "=COUNTBLANK(FlexLines[PlannedPrice])"
    rep.Range("B4:F18").NumberFormat = MONEY
    rep.Columns("A").ColumnWidth = 30
    rep.Columns("B:F").ColumnWidth = 16

    fp = xl.sheet(wb, "FurniturePrices", after=rep)
    heads = ["Month", "FlexRevenue", "LineTotal", "DiscountAmount", "ListAmount", "Planned", "Before promotions",
             "After promotions"]
    for i, h in enumerate(heads):
        fp.Cells(1, 1 + i).Value = h
    for m in range(1, 13):
        r = 1 + m
        fp.Cells(r, 1).Value = m
        for col, fld in zip("BCDE", ("FlexRevenue", "LineTotal", "DiscountAmount", "ListAmount")):
            fp.Range(f"{col}{r}").Formula2 = (f'=SUMIFS(FlexLines[{fld}],FlexLines[ItemGroup],"Furniture",'
                                              f"FlexLines[Month],$A{r})")
        formulas(fp, {f"F{r}": f"=B{r}/E{r}", f"G{r}": f"=(C{r}+D{r})/E{r}", f"H{r}": f"=C{r}/E{r}"})
    fp.Range("B2:E13").NumberFormat = MONEY
    fp.Range("F2:H13").NumberFormat = "0.0%"
    pchart = fp.Shapes.AddChart2(-1, xl.XL_LINE_MARKERS, fp.Range("J1").Left, fp.Range("J1").Top, 480, 288).Chart
    pchart.SetSourceData(fp.Range("F1:H13"))
    for i in range(1, 4):
        pchart.FullSeriesCollection(i).XValues = fp.Range("A2:A13")

    xl.add_query(wb, "GLOpex", nav(b, 3, "GLEntry", extra=[
        ("Filtered Rows", pq.select_rows(f"([FiscalYear] = {y})")),
        ("Merged Queries", pq.merge("Account", "AccountID", "AccountID", "Account")),
        ("Expanded Account", pq.expand("Account", ["AccountNumber", "AccountName"])),
        ("Filtered Rows1", pq.select_rows("[AccountNumber] >= 6000 and [AccountNumber] <= 7999")),
        ("Filtered Rows2", pq.select_rows(f'([VoucherNumber] <> "{close}")')),
        ("Added Custom", pq.add_custom("Amount", "[Debit] - [Credit]"))]))
    xl.load_query(wb, "GLOpex", "GLOpex", after=ws_(b, "FlexLines"))

    ox = xl.sheet(wb, "OpexReport", after=fp)
    values(ox, {"A4": "Account", "B4": "Name", "C4": "Budget", "D4": "Actual", "E4": "Variance",
                "G5": "Budgeted burden rate", "G6": "Actual burden rate", "G7": "Budgeted commission rate",
                "G8": "Flexed commission budget", "G9": "Actual commissions"})
    formulas(ox, {
        "A5": '=SORT(UNIQUE(FILTER(BudgetLine[AccountNumber],BudgetLine[BudgetCategory]="Operating Expense")))',
        "B5": "=XLOOKUP(A5#,Account[AccountNumber],Account[AccountName])",
        "C5": '=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],A5#,BudgetLine[BudgetCategory],"Operating Expense")',
        "D5": "=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],A5#)",
        "E5": "=D5#-C5#",
        "H5": ('=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],6060)/'
               'SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountName],"Salaries*")'),
        "H6": '=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],6060)/SUMIFS(GLOpex[Amount],GLOpex[AccountName],"Salaries*")',
        "H7": "=SUMIFS(BudgetLine[BudgetAmount],BudgetLine[AccountNumber],6290)/BudgetReport!F4",
        "H8": "=H7*BudgetReport!F10",
        "H9": "=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],6290)"})
    ox.Range("C5:E40").NumberFormat = MONEY
    ox.Range("H5:H7").NumberFormat = PCT
    ox.Range("H8:H9").NumberFormat = MONEY
    ox.Columns("B").ColumnWidth = 34
    ox.Columns("G").ColumnWidth = 26

    br = expected.budget_report(e, y)
    op = expected.opex(y, close)
    gsum = lambda k: sum(br["groups"][g][k] for g in groups)
    flexed = op["commission_budget"] / gsum("static_rev") * gsum("actual")
    fur = br["groups"]["Furniture"]
    b.doc["Query steps"] += (f" BudgetLine keeps fiscal {y} without the Balance Sheet lines, with ItemGroup from Item and "
                             "AccountNumber and AccountName from Account; Account keeps three columns; PlannedPrices "
                             "(not loaded) keeps each item's planned net price by month; FlexLines prices the "
                             f"{y} product lines at those prices ({br['missing']} lines have no planned price and keep "
                             f"their actual amount); GLOpex keeps the {y} postings to accounts 6000 to 7999 without the "
                             f"closing entry {close}.")
    b.sheets.update(BudgetLine=f"the {y} budget lines (query BudgetLine)", Account="the chart of accounts (query Account)",
                    FlexLines=f"the {y} product lines at the budget's planned prices (query FlexLines)",
                    GLOpex=f"the {y} operating-expense postings (query GLOpex)",
                    BudgetReport="the static budget, flexible budget, and actual results by product line",
                    FurniturePrices="planned and actual Furniture prices as a percentage of list, by month",
                    OpexReport="operating expenses against their budget, and the two driver tests")
    b.extra.append(["Finding", f"The sales-volume variance ({gsum('volume_var'):,.0f}) measures the budget's forecast, "
                    "which planned several times the units sold, so 2026 is judged against the flexible budget. Against "
                    f"it, every product line earned less than planned ({gsum('flex_var'):,.0f} in all): the planned "
                    "net prices were a few percent above what the price lists delivered, and Furniture adds the "
                    f"promotional discounts ({fur['discounts']:,.0f}), which came later than the budget planned them. "
                    f"Two expense assumptions did not hold: the payroll burden rate ({op['burden_budget']:.1%} budgeted, "
                    f"{op['burden_actual']:.1%} actual) and the commission budget, which flexes to {flexed:,.0f} against "
                    f"{op['commission_actual']:,.2f} paid."])
    write_documentation(b)

    t = "7.2"
    b.check(t, "lines without a planned price (BudgetReport!B20)", br["missing"], "=BudgetReport!B20", 0, COUNT)
    for addr, key in (("B6", "static_margin"), ("B9", "flex_margin"), ("B12", "actual_margin"), ("B13", "volume_var"),
                      ("B14", "flex_var"), ("B15", "discounts")):
        b.check(t, f"Furniture {key.replace('_', ' ')} (BudgetReport!{addr})", round(fur[key], 2),
                f"=BudgetReport!{addr}", 0.01)
    b.check(t, "static margin plus the two variances less the actual margin, total (column F)", 0,
            "=BudgetReport!F6+BudgetReport!F13+BudgetReport!F14-BudgetReport!F12", 0.01)
    b.check(t, "budgeted burden rate (OpexReport!H5)", round(op["burden_budget"], 9), "=OpexReport!H5", 1e-9, PCT)
    b.check(t, "actual burden rate (OpexReport!H6)", round(op["burden_actual"], 9), "=OpexReport!H6", 1e-9, PCT)
    b.check(t, "flexed commission budget (OpexReport!H8)", round(flexed, 2), "=OpexReport!H8", 0.01)
    b.check(t, "actual commissions (OpexReport!H9)", round(op["commission_actual"], 2), "=OpexReport!H9", 0.01)


def t7_3(b: Build) -> None:
    wb, e = b.wb, b.exp
    y = b.year
    close = YEAR_END_CLOSE.format(year=y)
    ws = xl.sheet(wb, "Model", after=ws_(b, "OpexReport"))
    labels = ["Discount rate", "Volume lift", "Units on promotion lines", "Price before discount per unit",
              "Variable cost per unit", "Commission rate"]
    names = ["Discount", "Lift", "PromoUnits", "PriceBeforeDiscount", "VariableCost", "CommissionRate"]
    sources = [f"PromotionProgram, promotion {PROMO}", "Assumption; order data shows none",
               f"InvoiceLines, promotion {PROMO}", f"InvoiceLines, promotion {PROMO}", "Standard cost per unit",
               f"Tutorial 7.2, actual {y}"]
    values(ws, {"A1": "Input or result", "B1": "Value", "C1": "Name", "D1": "Source"})
    for i, (label, name, src) in enumerate(zip(labels, names, sources)):
        r = 2 + i
        values(ws, {f"A{r}": label, f"C{r}": name, f"D{r}": src})
        xl.name_cell(wb, name, f"Model!$B${r}")
    for i, (label, name) in enumerate(zip(["Contribution without promotion", "Contribution with promotion",
                                           "Difference"], ["ContributionWithout", "ContributionWith", "Difference"])):
        r = 9 + i
        values(ws, {f"A{r}": label, f"C{r}": name, f"D{r}": "Formula"})
        xl.name_cell(wb, name, f"Model!$B${r}")
    values(ws, {"B2": 0.1, "B3": 0})
    ws.Range("B2:B3").NumberFormat = "0%"
    ws.Range("B2:B3").Font.Color = xl.BLUE
    formulas(ws, {
        "B4": f"=SUMIFS(InvoiceLines[Quantity],InvoiceLines[PromotionID],{PROMO})",
        "B5": (f"=(SUMIFS(InvoiceLines[LineTotal],InvoiceLines[PromotionID],{PROMO})+"
               f"SUMIFS(InvoiceLines[DiscountAmount],InvoiceLines[PromotionID],{PROMO}))/PromoUnits"),
        "B6": f"=SUMIFS(InvoiceLines[StdCostAmount],InvoiceLines[PromotionID],{PROMO})/PromoUnits",
        "B7": f"=SUMIFS(GLOpex[Amount],GLOpex[AccountNumber],6290)/SUMIFS(InvoiceLines[LineTotal],InvoiceLines[FiscalYear],{y})",
        "B9": "=PromoUnits*(PriceBeforeDiscount*(1-CommissionRate)-VariableCost)",
        "B10": "=PromoUnits*(1+Lift)*(PriceBeforeDiscount*(1-Discount)*(1-CommissionRate)-VariableCost)",
        "B11": "=ContributionWith-ContributionWithout"})
    ws.Range("B4:B6").NumberFormat = MONEY
    ws.Range("B7").NumberFormat = "0.000%"
    ws.Range("B9:B11").NumberFormat = MONEY

    scenarios = [("End the promotion", 0, 0), ("Repeat as in 2026", 0.1, 0), ("Repeat with 15% lift", 0.1, 0.15),
                 ("Deeper discount", 0.15, 0.15)]
    for name, disc, lift in scenarios:
        ws.Scenarios().Add(name, ws.Range("B2:B3"), [disc, lift])
    ws.Scenarios().CreateSummary(1, ws.Range("B10:B11"))          # xlStandardSummary: a Scenario Summary worksheet
    ws.Activate()

    ws.Range("A15").Formula = "=Difference"
    for col, d in zip("BCD", (0.05, 0.1, 0.15)):
        ws.Range(f"{col}15").Value = d
    for i in range(9):
        ws.Cells(16 + i, 1).Value = round(0.05 * i, 2)
    ws.Range("A15:D24").Table(ws.Range("B2"), ws.Range("B3"))
    ws.Range("B16:D24").NumberFormat = "#,##0"
    ws.Range("B15:D15").NumberFormat = "0%"
    ws.Range("A16:A24").NumberFormat = "0%"
    positive = ws.Range("B16:D24").FormatConditions.Add(1, 5, "=0")      # Cell Value > 0
    positive.Interior.Color = xl.LIGHT_FILL

    ws.Range("B11").GoalSeek(0, ws.Range("B3"))
    b.found["breakeven"] = ws.Range("B3").Value
    ws.Range("B3").Value = 0                                       # Step 6d: Cancel, so that B3 returns to 0

    cache = wb.PivotCaches().Create(SourceType=xl.XL_DATABASE, SourceData="SalesInvoiceLine")
    ov = xl.sheet(wb, "OrderVolume", after=ws)
    pt = cache.CreatePivotTable(TableDestination=ov.Range("A3"), TableName="PivotTable6")
    pt.PivotFields("ItemGroup").Orientation = xl.XL_PAGE
    pt.PivotFields("ItemGroup").CurrentPage = "Furniture"
    pt.PivotFields("OrderDate").Orientation = xl.XL_ROW
    pt.PivotFields("OrderDate").DataRange.Cells(1).Group(True, True, None,
                                                         (False, False, False, False, True, False, True))
    pt.AddDataField(pt.PivotFields("Quantity"), "Sum of Quantity", xl.XL_SUM).NumberFormat = MONEY

    pm = expected.promotion_model(e, PROMO, y, close)
    lift = b.found["breakeven"]
    table = [("Assumption", "Value used", "Basis", "Sensitivity"),
             ("Discount rate", "10%", "The promotion's DiscountPct in the PromotionProgram Table",
              "A 5% discount would need a much smaller lift to break even"),
             ("Volume lift", "0%", "Furniture orders in the promotion's months matched other months",
              f"The break-even lift is {lift:.1%} (Goal Seek), between the data table's 30% and 35% columns"),
             ("Orders without the promotion", "Same orders at the price before discount",
              "Promotion lines carry the customer's usual price, with the discount applied on top",
              "If some orders would have been lost without it, the promotion's cost is lower"),
             ("Variable cost per unit", "Standard cost per unit", "Item standard costs of the promotion's items",
              "Treating the fixed overhead in standard cost as fixed lowers the break-even lift slightly"),
             ("Commission rate", f"{y} actual rate",
              "Commission expense over all 2026 revenue, including design services, which earn a higher rate",
              "Small; commissions fall with the discount")]
    for i, row in enumerate(table):
        for j, v in enumerate(row):
            ws.Cells(27 + i, 1 + j).Value = v
    ws.Range("A27:D27").Font.Bold = True
    ws.Columns("A").ColumnWidth = 30
    ws.Columns("B").ColumnWidth = 16
    ws.Columns("C:D").ColumnWidth = 40

    b.doc["Parameters"] += (" Model: Discount and Lift (inputs, Model!B2:B3), PromoUnits, PriceBeforeDiscount, "
                            "VariableCost, CommissionRate (calculated, B4:B7), ContributionWithout, ContributionWith, "
                            "Difference (results, B9:B11).")
    b.sheets.update(Model="the promotion model, its data table, and its assumptions",
                    OrderVolume=f"Furniture units by order month (PivotTable of SalesInvoiceLine)")
    b.sheets["Scenario Summary"] = "the Scenario Manager summary of four scenarios"
    b.extra.append(["Recommendation", f"Do not repeat the promotion as it ran in {y}. At a 10% discount the promotion's "
                    f"orders would have needed {lift:.0%} more volume to pay for itself, and Furniture orders in its "
                    "months show no increase. A smaller discount, or one limited to the items and customers most "
                    "likely to respond, has a far lower bar; the recommendation would reverse only if a test showed a "
                    "volume response close to the break-even lift."])
    write_documentation(b)

    t = "7.3"
    for addr, key, fmt, tol in (("B4", "units", MONEY, 0.005), ("B5", "price", MONEY, 1e-6),
                                ("B6", "cost", MONEY, 1e-6), ("B7", "commission", RATIO, 1e-9)):
        b.check(t, f"{key} (Model!{addr})", round(pm[key], 9), f"=Model!{addr}", tol, fmt)
    b.check(t, "difference at a 10% discount and no lift (Model!B11)", round(pm["difference"](0.1, 0), 2),
            "=Model!B11", 0.01)
    b.check(t, "Goal Seek's break-even lift (Model, assumption table)", round(pm["breakeven"], 4), round(lift, 4),
            1e-4, PCT)
    b.check(t, "data table: 10% discount, 30% lift (Model!C22), still negative", round(pm["difference"](0.1, 0.3), 2),
            "=Model!C22", 0.01)
    b.check(t, "data table: 10% discount, 35% lift (Model!C23), positive", round(pm["difference"](0.1, 0.35), 2),
            "=Model!C23", 0.01)
    b.check(t, "the Scenario Summary worksheet exists", True, "=ISREF(INDIRECT(\"'Scenario Summary'!A1\"))", 0, "General")
    fq = sum(l["qty"] for l in e.lines if e.items[l["item"]]["group"] == "Furniture")
    b.check(t, "Furniture units ordered, all years (OrderVolume grand total)", round(fq, 2),
            '=GETPIVOTDATA("Sum of Quantity",OrderVolume!$A$3)', 0.01)


TUTORIALS = [("4.1", t4_1), ("4.2", t4_2), ("4.3", t4_3), ("5.1", t5_1), ("5.2", t5_2), ("5.3", t5_3),
             ("6.1", t6_1), ("6.2", t6_2), ("6.3", t6_3), ("7.1", t7_1), ("7.2", t7_2), ("7.3", t7_3)]
