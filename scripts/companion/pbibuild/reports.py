"""Charles River Reports.pbip: the reporting package Tutorials 13.1 to 15.3 build, and the appendix's Guided Tutorial
A.1 secures.

Each function applies one tutorial's steps to the project as the previous tutorial left it: the same queries (with
the Power Query Editor's step names and the type corrections the text asks for), relationships, column settings,
measures, pages, and visuals. A later tutorial changes what an earlier one built the way the reader does (Tutorial 14.1
re-points the visuals at the Date table and stops loading SalesInvoice). The DAX the text prints (the Date table, the
measures, the test queries, the role rules) is read from the tutorial .qmd files, so the file and the text cannot
drift. Each tutorial adds checks to the Checks DAX query tab: the values its checkpoint and its generated note state,
computed independently from CharlesRiver.sqlite.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import textwrap
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path

from paths import REPO, db_uri
from pbibuild.model import (DATE_FORMAT, MEASURES_TABLE, TMDL_TYPE, Column, Measure, Model, Query, Role, Table,
                            query_table)
from pbibuild.pbir import Page, Report, Visual, _ref, agg, col, lit, meas, textbox
from pbibuild.project import Check, Project
from xlbuild import pq
from xlbuild.expected import Expected

sys.path.insert(0, str(REPO / "facts"))
from db import Data  # noqa: E402
from notes import appendix_a, ch14, ch15  # noqa: E402

FILE = "Charles River Reports"
MONEY = "#,0.00"
COUNT = "#,0"
PCT = "0.00%"
CH13 = REPO / "chapters" / "13-power-bi-essentials"
CH14 = REPO / "chapters" / "14-data-models-and-dax"
CH15 = REPO / "chapters" / "15-management-reports"
APPX = REPO / "appendices" / "a-publishing-security"
TOP = 56                                   # visuals start below a band the page navigator of Tutorial 15.3 takes


@dataclass
class Build:
    xlsx: Path
    exp: Expected
    year: int
    project: Project = None
    queries: dict = field(default_factory=dict)
    tests: list[str] = field(default_factory=list)          # the queries of the Tests tab, in order
    role_checks: dict = field(default_factory=dict)         # label -> (role, effective user, checks): run under a role

    def __post_init__(self):
        self.project = Project(FILE, Model("Charles River Reports"), Report())

    @property
    def model(self) -> Model:
        return self.project.model

    @property
    def report(self) -> Report:
        return self.project.report

    def check(self, section: str, label: str, expected, dax: str, tolerance: float = 0.005) -> None:
        self.project.check(section, label, expected, dax, tolerance)

    @cached_property
    def data(self) -> Data:
        return Data()

    def query(self, name: str) -> Query:
        return self.model.tables[name].query if name in self.model.tables else self.model.staging[name]

    def add_tests(self, path: Path) -> None:
        """Type the tutorial's test queries at the end of the Tests tab (the tab the text renames, kept first)."""
        self.tests += dax_blocks(path, "query")
        self.project.queries["Tests"] = "\n\n".join(self.tests) + "\n"
        if "Checks" in self.project.queries:
            self.project.queries["Checks"] = self.project.queries.pop("Checks")


# --- the data (read-only) -------------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _con() -> sqlite3.Connection:
    return sqlite3.connect(db_uri(), uri=True, check_same_thread=False)


def rows(sql: str, *args) -> list[tuple]:
    return _con().execute(sql, args).fetchall()


def one(sql: str, *args):
    return _con().execute(sql, args).fetchone()[0]


LINES = ("FROM SalesInvoiceLine l JOIN SalesInvoice si ON si.SalesInvoiceID = l.SalesInvoiceID "
         "JOIN Item i ON i.ItemID = l.ItemID JOIN Customer c ON c.CustomerID = si.CustomerID ")


def sales(where: str = "1 = 1", *args) -> dict:
    """Invoice-line totals as the model sums them (the unrounded custom columns)."""
    r = rows("SELECT SUM(l.LineTotal), SUM(l.Quantity * l.BaseListPrice), SUM(l.Quantity * l.UnitPrice * l.Discount), "
             "COUNT(DISTINCT l.SalesInvoiceID), COUNT(*), SUM(l.Quantity * i.StandardCost), "
             "SUM(l.Quantity * l.UnitPrice) " + LINES + "WHERE " + where, *args)[0]
    return dict(rev=r[0] or 0.0, list=r[1] or 0.0, disc=r[2] or 0.0, invoices=r[3], lines=r[4], std=r[5] or 0.0,
                price=r[6] or 0.0)


def money(x: float) -> str:
    return f"{x:,.2f}"


# --- the text --------------------------------------------------------------------------------------------------------

def dax_blocks(path: Path, kind: str) -> list[str]:
    """The DAX blocks of a tutorial file marked <!-- dax-check: kind -->, in order, without their common indent."""
    text = path.read_text(encoding="utf-8")
    return [textwrap.dedent(m.group(1)).strip("\n") for m in
            re.finditer(r"<!-- dax-check: " + kind + r" -->\s*\n```\s*\n(.*?)\n```", text, re.S)]


def definitions(body: str) -> list[tuple[str, str]]:
    """(name, expression) of each definition in a block: a line `Name = ...` starts one, other lines continue it."""
    out = []
    for line in body.split("\n"):
        m = re.match(r"^([A-Za-z][\w &%()-]*?) =(?: (.*))?$", line)       # not a line such as Table[Col] = "x" )
        if m and not line.startswith(("VAR", "RETURN", "EVALUATE")):
            out.append((m.group(1).strip(), [m.group(2)] if m.group(2) else []))
        else:
            out[-1][1].append(line)
    return [(name, "\n".join(lines).strip("\n")) for name, lines in out]


def text_measures(path: Path, formats: dict[str, str | None], descriptions: dict[str, str] | None = None,
                  skip: tuple = ()) -> list[Measure]:
    """The measures a tutorial prints, in its order, with the formats the text asks for."""
    found = [d for body in dax_blocks(path, "measure") for d in definitions(body) if d[0] not in skip]
    assert [n for n, _ in found] == list(formats), f"{path.name}: measures {[n for n, _ in found]}"
    return [Measure(n, dax, formats[n], (descriptions or {}).get(n)) for n, dax in found]


def code_after(path: Path, marker: str) -> str:
    """The first plain code block after the line holding `marker` (a Power Query formula the text prints)."""
    text = path.read_text(encoding="utf-8")
    return re.search(r"```\s*\n(.*?)\n```", text[text.index(marker):], re.S).group(1).strip()


# --- model edits -----------------------------------------------------------------------------------------------------

def sync(table: Table, formats: dict[str, str] | None = None) -> Table:
    """Add a column for every query column the table lacks (after a merge, a custom column, or a column chosen again),
    typed and summarized as Desktop loads it."""
    have = {c.name for c in table.columns}
    for name, mtype in table.query.columns.items():
        if name not in have:
            dtype = TMDL_TYPE[mtype]
            table.columns.append(Column(name, dtype, fmt=(formats or {}).get(name) or
                                        (DATE_FORMAT if mtype == "type date" else None),
                                        summarize="sum" if dtype in ("int64", "double", "decimal") else "none"))
    return table


def hide(table: Table, *names: str) -> None:
    """Is hidden, and Summarize by None, as Tutorial 14.1 Step 7 sets them for keys."""
    for n in names:
        c = table.column(n)
        c.hidden, c.summarize = True, "none"


def rechoose(q: Query, add: list[str], xlsx: Path, sheet: str) -> None:
    """Reopen Choose Columns on the query's Removed Other Columns step (its settings icon) and select more columns:
    the step keeps the Table's column order, and the new columns pass through every later step."""
    i = next(i for i, (name, _) in enumerate(q.steps) if name == "Removed Other Columns")
    detected = dict(q.source[3])
    order = [c for c, _ in pq.detected_types(xlsx, sheet)]
    kept = [c for c in order if c in q.columns or c in add]
    q.steps[i] = ("Removed Other Columns", pq.select_columns(kept))
    q.columns = {c: (q.columns[c] if c in q.columns else detected[c]) for c in kept} | \
                {c: t for c, t in q.columns.items() if c not in kept}


def unrelate(m: Model, many: str, one_: str) -> None:
    before = len(m.relationships)
    m.relationships = [r for r in m.relationships if (r.from_column, r.to_column) != (many, one_)]
    assert len(m.relationships) == before - 1, f"no relationship {many} to {one_}"


def entered(name: str, columns: list[tuple[str, str]], data: list[list], hidden: bool = False) -> Table:
    """A table made with Home > Enter data, typed as Enter data detects its columns (whole numbers, text)."""
    return Table(name, [Column(c, t, summarize="sum" if t == "int64" else "none") for c, t in columns],
                 entered=data, hidden=hidden)


# --- report pieces ---------------------------------------------------------------------------------------------------

def literal(v) -> dict:
    if v is None:
        return {"Literal": {"Value": "null"}}
    if isinstance(v, bool):
        return {"Literal": {"Value": "true" if v else "false"}}
    if isinstance(v, int):
        return {"Literal": {"Value": f"{v}L"}}
    if isinstance(v, float):
        return {"Literal": {"Value": f"{v}D"}}
    return {"Literal": {"Value": "'" + str(v).replace("'", "''") + "'"}}


def _aliased(f: dict) -> tuple[str, str, dict]:
    kind = next(iter(f))
    entity = f[kind]["Expression"]["SourceRef"]["Entity"]
    alias = entity[0].lower()
    return entity, alias, {kind: {"Expression": {"SourceRef": {"Source": alias}}, "Property": f[kind]["Property"]}}


def condition(f: dict, values: list, exclude: bool = False) -> dict:
    entity, alias, ref = _aliased(f)
    cond = {"In": {"Expressions": [ref], "Values": [[literal(v)] for v in values]}}
    if exclude:
        cond = {"Not": {"Expression": cond}}
    return {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}], "Where": [{"Condition": cond}]}


def keep(name: str, f: dict, values: list, exclude: bool = False) -> dict:
    """Filters on this visual: a basic filter that keeps (or, inverted, excludes) the values."""
    out = {"name": name, "field": f, "type": "Categorical", "howCreated": "User", "filter": condition(f, values, exclude)}
    if exclude:
        out["objects"] = {"general": [{"properties": {"isInvertedSelectionMode": lit(True)}}]}
    return out


def slicer(name: str, x, y, w, h, f: dict, selected: list = (), style: str = "list", single: bool = False,
           title: str | None = None) -> Visual:
    """A slicer: Style Vertical list, Tile (horizontal), or Dropdown, with the values selected."""
    general = {}
    if style == "tile":
        general["orientation"] = lit(1)
    if selected:
        general["filter"] = {"filter": condition(f, list(selected))}
    objects = {"data": [{"properties": {"mode": lit("Dropdown" if style == "dropdown" else "Basic")}}]}
    if general:
        objects["general"] = [{"properties": general}]
    if single:
        objects["selection"] = [{"properties": {"strictSingleSelect": lit(True)}}]
    return Visual(name, "slicer", x, y, w, h, {"Values": [f]}, title=title, objects=objects)


def card(name: str, x, y, w, h, fields: list, units_none: bool = False, title: str | None = None,
         filters: list | None = None) -> Visual:
    """The card visual, one card for each value; Callout values > Display units None shows whole amounts."""
    objects = ({"value": [{"properties": {"labelDisplayUnits": lit(1)}, "selector": {"id": "default"}}]}
               if units_none else None)
    return Visual(name, "cardVisual", x, y, w, h, {"Data": fields}, title=title, objects=objects, filters=filters)


def value_axis(**props) -> dict:
    return {"valueAxis": [{"properties": {k: lit(v) for k, v in props.items()}}]}


def expanded(role: str, levels: list[dict], value) -> dict:
    """The matrix's `value` of the first level expanded with its plus sign."""
    refs = [_ref(f)[1] for f in levels]
    return {"expansionStates": [{
        "roles": [role],
        "levels": [{"queryRefs": [refs[0]], "isCollapsed": True, "identityKeys": [levels[0]], "isPinned": True}] +
                  [{"queryRefs": [r], "isCollapsed": True, "isPinned": True} for r in refs[1:]],
        "root": {"children": [{"identityValues": [literal(value)], "isToggled": True}]}}]}


def repoint(report: Report, mapping: dict[tuple[str, str], tuple[str, str]]) -> int:
    """Replace fields in every visual (wells, visual filters, slicer selections, sorts), as dragging the replacement
    onto the field does (Tutorial 14.1 Step 5). Returns the number of visuals changed."""
    def fix(o):
        if isinstance(o, list):
            return [fix(x) for x in o]
        if not isinstance(o, dict):
            return o
        if "From" in o and "Where" in o:
            (frm,) = o["From"]
            box = {"entity": frm["Entity"]}
            where = fix_where(o["Where"], frm, box)
            return {**o, "From": [{**frm, "Entity": box["entity"]}], "Where": where}
        if "Column" in o and "Entity" in o["Column"]["Expression"].get("SourceRef", {}):
            key = (o["Column"]["Expression"]["SourceRef"]["Entity"], o["Column"]["Property"])
            if key in mapping:
                return col(*mapping[key])
        return {k: fix(v) for k, v in o.items()}

    def fix_where(o, frm, box):
        if isinstance(o, list):
            return [fix_where(x, frm, box) for x in o]
        if not isinstance(o, dict):
            return o
        if "Column" in o and o["Column"]["Expression"].get("SourceRef", {}).get("Source") == frm["Name"]:
            key = (frm["Entity"], o["Column"]["Property"])
            if key in mapping:
                box["entity"] = mapping[key][0]
                return {"Column": {"Expression": {"SourceRef": {"Source": frm["Name"]}}, "Property": mapping[key][1]}}
        return {k: fix_where(v, frm, box) for k, v in o.items()}

    changed = 0
    for page in report.pages:
        for v in page.visuals:
            before = repr((v.roles, v.filters, v.sort, v.objects, v.extra))
            v.roles = {r: [(fix(f[0]), f[1]) if isinstance(f, tuple) else fix(f) for f in fs]
                       for r, fs in v.roles.items()}
            v.filters = fix(v.filters) if v.filters else v.filters
            v.sort = [(fix(f), d) for f, d in v.sort] if v.sort else v.sort
            v.objects = fix(v.objects) if v.objects else v.objects
            v.extra = fix(v.extra) if v.extra else v.extra
            changed += before != repr((v.roles, v.filters, v.sort, v.objects, v.extra))
    return changed


def t13_1(b: Build) -> None:
    e, y = b.exp, b.year
    customer = Query.navigator("Customer", b.xlsx, 4, "Customer").select(
        ["CustomerID", "CustomerName", "CustomerSegment", "Region"])
    invoice = (Query.navigator("SalesInvoice", b.xlsx, 16, "SalesInvoice")
               .select(["SalesInvoiceID", "InvoiceNumber", "InvoiceDate", "CustomerID"])
               .types({"InvoiceDate": "type date"}))
    lines = Query.navigator("SalesInvoiceLine", b.xlsx, 17, "SalesInvoiceLine",
                            corrections={"Discount": "type number", "PromotionID": "Int64.Type"}).select(
        ["SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "Quantity", "BaseListPrice", "UnitPrice", "Discount",
         "LineTotal", "PromotionID", "PricingMethod"])
    item = (Query.navigator("Item", b.xlsx, 44, "Item")
            .select(["ItemID", "ItemCode", "ItemName", "ItemGroup", "StandardCost", "ListPrice"])
            .filter("([ListPrice] <> null)"))
    # Step 5: the custom columns, then their types
    invoice.custom("FiscalYear", "Date.Year([InvoiceDate])").custom(
        "FiscalQuarter", "Date.QuarterOfYear([InvoiceDate])").custom(
        "Period", 'Text.From([FiscalYear]) & "-Q" & Text.From([FiscalQuarter])').custom(
        "Month", 'Date.ToText([InvoiceDate], "yyyy-MM")').types(
        {"FiscalYear": "Int64.Type", "FiscalQuarter": "Int64.Type", "Period": "type text", "Month": "type text"})
    lines.custom("ListAmount", "[Quantity] * [BaseListPrice]").custom(
        "DiscountAmount", "[Quantity] * [UnitPrice] * [Discount]").types(
        {"ListAmount": "type number", "DiscountAmount": "type number"})
    item.custom("ProductType", "Text.Middle([ItemCode], 4, 3)").types({"ProductType": "type text"})
    m = b.model
    m.add(query_table(customer))
    m.add(query_table(invoice, summarize={"FiscalYear": "none", "FiscalQuarter": "none"}))
    m.add(query_table(lines, formats={"LineTotal": MONEY, "ListAmount": MONEY, "DiscountAmount": MONEY}))
    m.add(query_table(item))
    m.relate("SalesInvoiceLine.SalesInvoiceID", "SalesInvoice.SalesInvoiceID")
    m.relate("SalesInvoiceLine.ItemID", "Item.ItemID")
    m.relate("SalesInvoice.CustomerID", "Customer.CustomerID")

    page = b.report.add(Page("validation", "Validation"))
    page.add(Visual("byYear", "tableEx", 20, 20, 760, 240, {"Values": [
        col("SalesInvoice", "FiscalYear"), agg("SalesInvoiceLine", "SalesInvoiceLineID", "count"),
        agg("SalesInvoiceLine", "LineTotal"), agg("SalesInvoiceLine", "ListAmount"),
        agg("SalesInvoiceLine", "DiscountAmount")]}))
    page.add(Visual("byGroup", "tableEx", 20, 290, 420, 260, {"Values": [
        col("Item", "ItemGroup"), agg("SalesInvoiceLine", "LineTotal")]}))
    current = round(sum(l["lt"] for l in e.lines if e.invoices[l["inv"]]["date"][:4] == str(y)), 2)
    page.expect = ["Count of SalesInvoiceLineID", "ItemGroup", f"{current:,.2f}"]

    c = e.control
    t = "Tutorial 13.1"
    b.check(t, "SalesInvoiceLine rows", c["lines"], "COUNTROWS ( SalesInvoiceLine )", 0)
    b.check(t, "SalesInvoice rows", c["invoices"], "COUNTROWS ( SalesInvoice )", 0)
    b.check(t, "Item rows (items with a list price)", c["items_sold"], "COUNTROWS ( 'Item' )", 0)
    b.check(t, "Customer rows", len(e.customers), "COUNTROWS ( Customer )", 0)
    for fy in range(y - 2, y + 1):
        ls = [l for l in e.lines if e.invoices[l["inv"]]["date"][:4] == str(fy)]
        f = f"SalesInvoice[FiscalYear] = {fy}"
        b.check(t, f"{fy} invoice lines", len(ls), f"CALCULATE ( COUNTROWS ( SalesInvoiceLine ), {f} )", 0)
        b.check(t, f"{fy} line total", round(sum(l["lt"] for l in ls), 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ), {f} )")
        b.check(t, f"{fy} list amount", round(sum(l["qty"] * l["blp"] for l in ls), 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[ListAmount] ), {f} )", 0.01)
        b.check(t, f"{fy} discounts", round(sum(l["qty"] * l["up"] * l["disc"] for l in ls), 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {f} )", 0.01)
    b.check(t, "invoice lines with no item (a (Blank) item group)", 0,
            "COUNTROWS ( FILTER ( SalesInvoiceLine, ISBLANK ( RELATED ( 'Item'[ItemGroup] ) ) ) )", 0)
    b.check(t, "item groups", 5, "COUNTROWS ( VALUES ( 'Item'[ItemGroup] ) )", 0)


def claim(ok: bool, text: str) -> None:
    """A statement the tutorial text makes about the data: if the data no longer bear it out, the text must change."""
    if not ok:
        raise SystemExit(f"The text no longer fits the data: {text}")


def month_sums(where: str, *args) -> dict[str, tuple[float, float]]:
    """(revenue, discounts) by invoice month."""
    return {r[0]: (r[1], r[2]) for r in rows("SELECT substr(si.InvoiceDate, 1, 7), SUM(l.LineTotal), "
                                             "SUM(l.Quantity * l.UnitPrice * l.Discount) " + LINES + "WHERE " + where +
                                             " GROUP BY 1", *args)}


def t13_2(b: Build) -> None:
    y = b.year
    page = b.report.add(Page("salesDiscounts", "Sales and Discounts"), before="validation")
    lt, la, da = (agg("SalesInvoiceLine", c) for c in ("LineTotal", "ListAmount", "DiscountAmount"))
    page.add(slicer("yearSlicer", 20, TOP, 320, 64, col("SalesInvoice", "FiscalYear"), [y], style="tile", single=True))
    page.add(slicer("segmentSlicer", 360, TOP, 220, 64, col("Customer", "CustomerSegment"), style="dropdown"))
    page.add(slicer("regionSlicer", 600, TOP, 220, 64, col("Customer", "Region"), style="dropdown"))
    page.add(card("salesCards", 20, TOP + 74, 1240, 96, [
        (lt, "Revenue"), (la, "At list price"), (da, "Discounts"),
        (agg("SalesInvoiceLine", "SalesInvoiceID", "distinctcount"), "Invoices")], units_none=True))
    page.add(Visual("discountsByMonth", "lineChart", 20, 240, 610, 220,
                    {"Category": [col("SalesInvoice", "Month")], "Y": [da]}, title="Promotional discounts by month"))
    page.add(Visual("discountsByGroup", "clusteredBarChart", 650, 240, 610, 220,
                    {"Category": [col("Item", "ItemGroup")], "Y": [da]}, title="Promotional discounts by item group"))
    levels = [col("Item", "ItemGroup"), col("Item", "ProductType")]
    page.add(Visual("revenueMatrix", "pivotTable", 20, 470, 1240, 240,
                    {"Rows": levels, "Columns": [col("SalesInvoice", "Period")], "Values": [lt]},
                    extra=expanded("Rows", levels, "Furniture"), active=("Rows",)))

    year = "substr(si.InvoiceDate, 1, 4) = ?"
    s, f = sales(year, str(y)), sales(year + " AND i.ItemGroup = 'Furniture'", str(y))
    months = month_sums(year, str(y))
    groups = dict(rows("SELECT i.ItemGroup, SUM(l.Quantity * l.UnitPrice * l.Discount) " + LINES + "WHERE " + year +
                       " GROUP BY 1", str(y)))
    trade = month_sums(year + " AND c.CustomerSegment = 'Design Trade'", str(y))
    quarters = {q: sales(year + " AND i.ItemGroup = 'Furniture' AND (CAST(substr(si.InvoiceDate, 6, 2) AS INTEGER) + 2) "
                               "/ 3 = ?", str(y), q)["rev"] for q in range(1, 5)}
    autumn = [f"{y}-09", f"{y}-10"]
    claim(max(d for m, (_, d) in months.items() if m < autumn[0]) < 0.2 * min(months[m][1] for m in autumn),
          "the discount line is close to zero through August and rises sharply in September and October")
    claim(groups["Furniture"] > 0.9 * sum(groups.values()), "almost all of the year's discounts were on Furniture")
    claim(max(trade, key=lambda m: trade[m][1]) == f"{y}-11", "with Design Trade selected, the discounts peak in November")
    types = [r[0] for r in rows("SELECT DISTINCT substr(ItemCode, 5, 3) FROM Item WHERE ItemGroup = 'Furniture' "
                                "AND ListPrice IS NOT NULL ORDER BY 1")]
    page.expect = ["Promotional discounts by month", "Promotional discounts by item group", money(s["rev"]),
                   money(quarters[1]), "Expanded Furniture", types[0], types[-1]]

    t, fy = "Tutorial 13.2", f"SalesInvoice[FiscalYear] = {y}"
    furn = "'Item'[ItemGroup] = \"Furniture\""
    for label, key, dax, tol in [("Revenue", "rev", "SUM ( SalesInvoiceLine[LineTotal] )", 0.005),
                                 ("At list price", "list", "SUM ( SalesInvoiceLine[ListAmount] )", 0.01),
                                 ("Discounts", "disc", "SUM ( SalesInvoiceLine[DiscountAmount] )", 0.01),
                                 ("Invoices", "invoices", "DISTINCTCOUNT ( SalesInvoiceLine[SalesInvoiceID] )", 0)]:
        b.check(t, f"{y} card {label}", round(s[key], 2), f"CALCULATE ( {dax}, {fy} )", tol)
        b.check(t, f"{y} card {label}, Furniture selected", round(f[key], 2), f"CALCULATE ( {dax}, {fy}, {furn} )", tol)
    b.check(t, f"{y} invoices counted from SalesInvoice, Furniture selected (the filter stops)",
            one("SELECT COUNT(*) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 4) = ?", str(y)),
            f"CALCULATE ( DISTINCTCOUNT ( SalesInvoice[SalesInvoiceID] ), {fy}, {furn} )", 0)
    for m in autumn + [f"{y}-11", f"{y}-12"]:
        b.check(t, f"discounts {m}", round(months[m][1], 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SalesInvoice[Month] = \"{m}\" )", 0.01)
    b.check(t, f"{y} discounts on Furniture", round(groups["Furniture"], 2),
            f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), {fy}, {furn} )", 0.01)
    b.check(t, f"{y}-11 discounts, Design Trade selected", round(trade[f"{y}-11"][1], 2),
            f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SalesInvoice[Month] = \"{y}-11\", "
            "Customer[CustomerSegment] = \"Design Trade\" )", 0.01)
    for q, v in quarters.items():
        b.check(t, f"Furniture revenue {y}-Q{q} (matrix)", round(v, 2),
                f"CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ), SalesInvoice[Period] = \"{y}-Q{q}\", {furn} )")


def t13_3(b: Build) -> None:
    y, first = b.year, b.year - 2
    page = b.report.add(Page("review", "Review"))
    month, fy = col("SalesInvoice", "Month"), col("SalesInvoice", "FiscalYear")
    lt, da = agg("SalesInvoiceLine", "LineTotal"), agg("SalesInvoiceLine", "DiscountAmount")
    months = month_sums("1 = 1")
    current = {m: v for m, v in months.items() if m.startswith(str(y))}
    low, high = min(current, key=lambda m: current[m][0]), max(current, key=lambda m: current[m][0])
    peak = max(current, key=lambda m: current[m][1])
    years = {fy_: sales("substr(si.InvoiceDate, 1, 4) = ?", str(fy_))["rev"] for fy_ in range(first, y + 1)}
    claim(peak == f"{y}-10", "October is the month of the largest discounts")
    claim(current[peak][1] < 0.1 * current[peak][0], "even in October, discounts were a small fraction of revenue")
    claim(abs(years[y] / years[y - 1] - 1) < 0.02, f"almost no growth from fiscal {y - 1} to fiscal {y}")
    claim((current[high][0] - current[low][0]) < 0.25 * sum(v[0] for v in current.values()) / len(current),
          "the gap between the weakest and the strongest month is a small fraction of a month's revenue")
    page.add(Visual("monthlyRevenue", "lineChart", 20, TOP, 610, 300, {"Category": [month], "Y": [lt]},
                    title=f"Monthly revenue, fiscal {y}", objects=value_axis(start=0),
                    filters=[keep("monthlyRevenueYear", fy, [y])],
                    alt_text=f"Monthly revenue in fiscal {y} on an axis from zero. Revenue varied little from month "
                             "to month."))
    page.add(Visual("revenueByYear", "clusteredColumnChart", 650, TOP, 610, 300, {"Category": [fy], "Y": [lt]},
                    title=f"Revenue by fiscal year, {first} to {y}",
                    objects={"labels": [{"properties": {"show": lit(True)}}]},
                    alt_text=f"Revenue by fiscal year from {first} to {y}. Revenue grew from {first} to {first + 1}, "
                             f"a year that includes the start-up month, and almost not at all from {y - 1} to {y}."))
    page.add(Visual("revenueAndDiscounts", "lineChart", 20, 366, 1240, 170, {"Category": [month], "Y": [lt, da]},
                    title=f"Revenue and promotional discounts by month, fiscal {y}",
                    filters=[keep("revenueAndDiscountsYear", fy, [y])],
                    alt_text=f"Revenue and promotional discounts by month in fiscal {y}, on one axis. Even in "
                             "October, the month of the largest discounts, they were a small fraction of revenue."))
    page.add(Visual("discountsOwnScale", "lineChart", 20, 546, 1240, 164, {"Category": [month], "Y": [da]},
                    title=f"Promotional discounts by month, fiscal {y}", objects=value_axis(showAxisTitle=True),
                    filters=[keep("discountsOwnScaleYear", fy, [y])],
                    alt_text=f"Promotional discounts by month in fiscal {y}, on their own scale. The discounts "
                             "peaked in September and October."))
    page.expect = [f"Monthly revenue, fiscal {y}", f"Revenue by fiscal year, {first} to {y}",
                   f"Revenue and promotional discounts by month, fiscal {y}",
                   f"Promotional discounts by month, fiscal {y}"]

    t = "Tutorial 13.3"
    rev = "CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ), SalesInvoice[Month] = \"{}\" )"
    for label, m in [(f"weakest month of {y}", low), (f"strongest month of {y}", high), ("start-up month", f"{first}-01"),
                     ("second month", f"{first}-02"), (f"last month of {y}", f"{y}-12"), ("largest discounts", peak)]:
        b.check(t, f"revenue {m} ({label})", round(months[m][0], 2), rev.format(m))
    b.check(t, f"discounts {peak}", round(months[peak][1], 2),
            f"CALCULATE ( SUM ( SalesInvoiceLine[DiscountAmount] ), SalesInvoice[Month] = \"{peak}\" )", 0.01)
    b.check(t, f"invoices in {first}-01 (start-up month)",
            one("SELECT COUNT(*) FROM SalesInvoice WHERE substr(InvoiceDate, 1, 7) = ?", f"{first}-01"),
            f"CALCULATE ( DISTINCTCOUNT ( SalesInvoiceLine[SalesInvoiceID] ), SalesInvoice[Month] = \"{first}-01\" )", 0)


def t14_1(b: Build) -> None:
    m, path = b.model, CH14 / "_tutorial-01.qmd"
    ctx = ch14.t1(b.data, claim)
    # Step 1: the invoice's number, date, and customer merged into the lines
    invoice, lines = b.query("SalesInvoice"), m.tables["SalesInvoiceLine"]
    lines.query.merge(invoice, "SalesInvoiceID", "SalesInvoiceID", ["InvoiceNumber", "InvoiceDate", "CustomerID"])
    sync(lines)
    # Steps 2 and 3: the Date table as the text prints it, Date typed as a date, MonthName sorted, marked
    ((name, expr),) = definitions(dax_blocks(path, "table")[0])
    assert name == "Date"
    m.add(Table("Date", [
        Column("Date", "dateTime", "[Date]", DATE_FORMAT, extra=("isKey",)),
        Column("Year", "int64", "[Year]", summarize="sum"), Column("Quarter", "string", "[Quarter]"),
        Column("YearQuarter", "string", "[YearQuarter]"), Column("YearMonth", "string", "[YearMonth]"),
        Column("MonthNumber", "int64", "[MonthNumber]", summarize="sum"),
        Column("MonthName", "string", "[MonthName]", sort_by="MonthNumber")], dax=expr, props=("dataCategory: Time",)))
    # Step 4: the star
    unrelate(m, "SalesInvoiceLine.SalesInvoiceID", "SalesInvoice.SalesInvoiceID")
    unrelate(m, "SalesInvoice.CustomerID", "Customer.CustomerID")
    m.relate("SalesInvoiceLine.InvoiceDate", "Date.Date")
    m.relate("SalesInvoiceLine.CustomerID", "Customer.CustomerID")
    # Step 5: the visuals take their periods from the Date table (tbl-14-02)
    swaps = {("SalesInvoice", "FiscalYear"): ("Date", "Year"), ("SalesInvoice", "Period"): ("Date", "YearQuarter"),
             ("SalesInvoice", "Month"): ("Date", "YearMonth")}
    repoint(b.report, swaps)
    # Step 6: SalesInvoice stays in Power Query only; no visual may still use it
    del m.tables["SalesInvoice"]
    m.stage(invoice)
    left = [f"{p.display}: {v.name}" for p in b.report.pages for v in p.visuals
            if '"Entity": "SalesInvoice"' in json.dumps(v.doc(0))]
    assert not left, f"visuals still use SalesInvoice: {left}"
    # Step 7: the keys hidden
    hide(lines, "SalesInvoiceLineID", "SalesInvoiceID", "ItemID", "CustomerID")
    hide(m.tables["Item"], "ItemID")
    hide(m.tables["Customer"], "CustomerID")
    b.report.page("validation").expect.append("Year")

    # The earlier checks now read the Date table, as the re-pointed visuals do; the two that counted the SalesInvoice
    # table itself go with it (its row count, and Tutorial 13.2's count that a filter on Item does not reach).
    kept = []
    for section, c in b.project.checks:
        for (t_, c_), (t2, c2) in swaps.items():
            c.dax = c.dax.replace(f"{t_}[{c_}]", f"'{t2}'[{c2}]")
        if not re.search(r"\bSalesInvoice\b", c.dax):
            kept.append((section, c))
    b.project.checks = kept
    t = "Tutorial 14.1"
    b.check(t, "Date rows (one per day)", ctx["days"], "COUNTROWS ( 'Date' )", 0)
    b.check(t, "first date", ctx["first"], "FORMAT ( MIN ( 'Date'[Date] ), \"yyyy-mm-dd\" )")
    b.check(t, "last date", ctx["last"], "FORMAT ( MAX ( 'Date'[Date] ), \"yyyy-mm-dd\" )")
    b.check(t, "invoice lines after the merge", ctx["n_lines"], "COUNTROWS ( SalesInvoiceLine )", 0)
    b.check(t, "lines that found no invoice", 0,
            "COUNTROWS ( FILTER ( SalesInvoiceLine, ISBLANK ( SalesInvoiceLine[InvoiceDate] ) ) )", 0)
    b.check(t, "lines with no Date row", 0,
            "COUNTROWS ( FILTER ( SalesInvoiceLine, ISBLANK ( RELATED ( 'Date'[Year] ) ) ) )", 0)
    b.check(t, "lines with no customer", 0,
            "COUNTROWS ( FILTER ( SalesInvoiceLine, ISBLANK ( RELATED ( Customer[CustomerName] ) ) ) )", 0)
    for yr in ctx["years"]:
        b.check(t, f"{yr['year']} invoices (distinct on the lines)", yr["invoices"],
                f"CALCULATE ( DISTINCTCOUNT ( SalesInvoiceLine[SalesInvoiceID] ), 'Date'[Year] = {yr['year']} )", 0)
    month = f"{b.year}-10"
    b.check(t, f"Month and YearMonth agree ({month})",
            round(sales("substr(si.InvoiceDate, 1, 7) = ?", month)["rev"], 2),
            f"CALCULATE ( SUM ( SalesInvoiceLine[LineTotal] ), 'Date'[YearMonth] = \"{month}\" )")


DESCRIPTIONS = {
    "Revenue": "Invoiced revenue: the sum of LineTotal on the invoice lines.",
    "List Amount": "The invoice lines at list price: the sum of Quantity times BaseListPrice.",
    "Discounts": "Promotional discounts: the sum of DiscountAmount on the invoice lines.",
    "Invoice Lines": "The number of invoice lines.",
    "Invoices": "The number of distinct invoices among the invoice lines in the filter context.",
    "Standard Cost": "Quantity times the item's standard cost, line by line.",
    "Gross Margin": "Revenue less standard cost.",
    "Margin %": "Gross margin as a share of revenue, calculated from the totals.",
    "Price Before Discount": "Quantity times unit price, line by line: the dollars the discounts were taken from.",
    "Discount Rate": "Discounts divided by the price before discount.",
    "Furniture Revenue": "Revenue of the Furniture item group, whatever item group is selected.",
    "Share of Revenue": "Revenue as a share of all item groups' revenue in the same period.",
}


def t14_2(b: Build) -> None:
    m, y, path = b.model, b.year, CH14 / "_tutorial-02.qmd"
    ctx = ch14.t2(b.data, claim)
    # Steps 1 to 5: the measures table (Enter data, its one column hidden) and the measures as the text prints them
    mt = m.add(entered(MEASURES_TABLE, [("Column1", "string")], []))
    m.query_order.append(MEASURES_TABLE)
    hide(mt, "Column1")
    formats = {"Revenue": MONEY, "List Amount": MONEY, "Discounts": MONEY, "Invoice Lines": COUNT, "Invoices": COUNT,
               "Standard Cost": MONEY, "Gross Margin": MONEY, "Margin %": PCT, "Price Before Discount": MONEY,
               "Discount Rate": PCT, "Furniture Revenue": MONEY, "Share of Revenue": PCT}
    mt.measures += text_measures(path, formats, DESCRIPTIONS)                 # Step 9: the descriptions
    M = lambda n: meas(MEASURES_TABLE, n)
    # Steps 5 and 6: the Margins page
    page = b.report.add(Page("margins", "Margins"))
    page.add(slicer("marginsYear", 20, TOP, 180, 150, col("Date", "Year"), [y]))
    page.add(Visual("groupShares", "tableEx", 220, TOP, 640, 220, {"Values": [
        col("Item", "ItemGroup"), M("Revenue"), M("Furniture Revenue"), M("Share of Revenue")]}))
    page.add(Visual("marginMatrix", "pivotTable", 20, 300, 1240, 260, {
        "Rows": [col("Item", "ItemGroup")], "Columns": [col("Date", "YearQuarter")], "Values": [M("Margin %")]},
        filters=[keep("marginMatrixYears", col("Date", "Year"), [y - 1, y])]))
    page.extra = {"visualInteractions": [{"source": "marginsYear", "target": "marginMatrix", "type": "NoFilter"}]}
    furniture_share = dict(ctx["shares"])["Furniture"]
    page.expect = ["Furniture Revenue", "Share of Revenue", money(ctx["furniture"]), f"{furniture_share:.2%}",
                   f"{y - 1}-Q1", f"{ctx['quarters'][-1]['pct']:.2%}"]
    # Steps 7 and 8: the Tests tab
    b.add_tests(path)
    # Step 9: the new measures beside the control totals on the Validation page
    v = next(v for v in b.report.page("validation").visuals if v.name == "byYear")
    v.roles["Values"] += [M("Invoices"), M("Standard Cost"), M("Margin %")]

    t, cy = "Tutorial 14.2", f"'Date'[Year] = {y}"
    furn = "'Item'[ItemGroup] = \"Furniture\""
    claim(ctx["rate"] > ctx["average"], "the discount rate is well above the average of the Discount column")
    claim(furniture_share > 0.5, "Furniture holds more than half of the year's revenue")
    q = ctx["quarters"]
    claim(q[-1]["pct"] < q[-2]["pct"] < min(x["pct"] for x in q[4:6]) and q[-1]["pct"] == min(x["pct"] for x in q),
          "Furniture's margin falls in the third quarter and again in the fourth, to its lowest of the two years")
    for label, key, dax, tol in [("Revenue", "rev", "[Revenue]", 0.005), ("Invoice Lines", "n", "[Invoice Lines]", 0),
                                 ("Invoices", "invoices", "[Invoices]", 0), ("Standard Cost", "cost", "[Standard Cost]", 0.01),
                                 ("Gross Margin", "gm", "[Gross Margin]", 0.01)]:
        b.check(t, f"{y} {label}", round(ctx[key], 2), f"CALCULATE ( {dax}, {cy} )", tol)
    for yr, pct in ctx["pct"].items():
        b.check(t, f"{yr} Margin %", round(pct, 6), f"CALCULATE ( [Margin %], 'Date'[Year] = {yr} )", 0.000005)
    b.check(t, f"{y} Discount Rate", round(ctx["rate"], 6), f"CALCULATE ( [Discount Rate], {cy} )", 0.000005)
    b.check(t, f"{y} average of the Discount column (Chapter 13)", round(ctx["average"], 6),
            f"CALCULATE ( AVERAGE ( SalesInvoiceLine[Discount] ), {cy} )", 0.000005)
    for g, share in ctx["shares"]:
        b.check(t, f"{y} Share of Revenue, {g}", round(share, 6),
                f"CALCULATE ( [Share of Revenue], {cy}, 'Item'[ItemGroup] = \"{g}\" )", 0.000005)
    b.check(t, f"{y} shares add up to 100%", 1, f"CALCULATE ( SUMX ( VALUES ( 'Item'[ItemGroup] ), [Share of Revenue] ), "
                                                f"{cy} )", 0.000001)
    b.check(t, f"{y} Furniture Revenue on the Lighting row", round(ctx["furniture"], 2),
            f"CALCULATE ( [Furniture Revenue], {cy}, 'Item'[ItemGroup] = \"Lighting\" )")
    b.check(t, f"{y} Furniture share with ALL ( SalesInvoiceLine ) instead", round(ctx["all_share"], 6),
            f"CALCULATE ( DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALL ( SalesInvoiceLine ) ) ), {cy}, {furn} )",
            0.000005)
    for i, x in enumerate(q):
        yq = f"{y - 1 + i // 4}-Q{i % 4 + 1}"
        b.check(t, f"Furniture Margin % {yq}", round(x["pct"], 6),
                f"CALCULATE ( [Margin %], 'Date'[YearQuarter] = \"{yq}\", {furn} )", 0.000005)
    for i, rate in enumerate(ctx["rates"]):
        b.check(t, f"Furniture Discount Rate {y}-Q{i + 1}", round(rate, 6),
                f"CALCULATE ( [Discount Rate], 'Date'[YearQuarter] = \"{y}-Q{i + 1}\", {furn} )", 0.000005)


def t14_3(b: Build) -> None:
    m, y, path = b.model, b.year, CH14 / "_tutorial-03.qmd"
    ctx = ch14.t3(b.data, claim)
    # Steps 1 to 3: the ledger's Tables, the columns kept, the closes flagged
    gl = (Query.navigator("GLEntry", b.xlsx, 3, "GLEntry")
          .select(["GLEntryID", "PostingDate", "AccountID", "Debit", "Credit", "VoucherNumber", "SourceDocumentType",
                   "CostCenterID"]).types({"PostingDate": "type date"}))
    account = Query.navigator("Account", b.xlsx, 1, "Account").select(
        ["AccountID", "AccountNumber", "AccountName", "AccountType", "AccountSubType", "NormalBalance"])
    center = Query.navigator("CostCenter", b.xlsx, 75, "CostCenter").select(["CostCenterID", "CostCenterName"])
    journal = Query.navigator("JournalEntry", b.xlsx, 2, "JournalEntry").select(["EntryNumber", "EntryType"])
    gl.merge(journal, "VoucherNumber", "EntryNumber", ["EntryType"])
    gl.custom("IsYearEndClose", code_after(path, "name the column `IsYearEndClose`"), "type logical")
    m.add(query_table(account))
    m.stage(journal)
    ledger = m.add(query_table(gl))
    m.add(query_table(center))
    # Step 4: the second star, sharing Date
    m.relate("GLEntry.AccountID", "Account.AccountID")
    m.relate("GLEntry.CostCenterID", "CostCenter.CostCenterID")
    m.relate("GLEntry.PostingDate", "Date.Date")
    hide(ledger, "GLEntryID", "AccountID", "CostCenterID")
    # Steps 5 and 7: the ledger's measures (Step 6's temporary Net Income with Closes is deleted again)
    m.tables[MEASURES_TABLE].measures += text_measures(path, {
        "GL Amount": MONEY, "P&L Amount": MONEY, "Net Income": MONEY, "Operating Expense": MONEY,
        "Expected Operating Expense": MONEY, "Operating Expense Deviation": "0.0%"}, skip=("Net Income with Closes",))
    M = lambda n: meas(MEASURES_TABLE, n)
    years = [y - 2, y - 1, y]
    # Steps 6 and 8: the Income Statement page
    page = b.report.add(Page("incomeStatement", "Income Statement"))
    levels = [col("Account", "AccountType"), col("Account", "AccountSubType")]
    page.add(Visual("incomeMatrix", "pivotTable", 20, TOP, 760, 330,
                    {"Rows": levels, "Columns": [col("Date", "Year")], "Values": [M("P&L Amount")]},
                    filters=[keep("incomeMatrixTypes", levels[0], ["Revenue", "Expense"]),
                             keep("incomeMatrixYears", col("Date", "Year"), years)],
                    extra={"expansionStates": [{"roles": ["Rows"], "levels": [
                        {"queryRefs": ["Account.AccountType"], "isCollapsed": False, "identityKeys": [levels[0]],
                         "isPinned": True}, {"queryRefs": ["Account.AccountSubType"], "isCollapsed": True,
                                             "isPinned": True}]}]}, active=("Rows",)))
    page.add(card("netIncomeCard", 800, TOP, 220, 110, [M("Net Income")],
                  filters=[keep("netIncomeCardYear", col("Date", "Year"), [y])]))
    page.add(Visual("expenseLine", "lineChart", 20, 400, 760, 310,
                    {"Category": [col("Date", "YearMonth")], "Y": [M("Operating Expense"), M("Expected Operating Expense")]},
                    filters=[keep("expenseLineYears", col("Date", "Year"), years)]))
    page.add(Visual("deviationTable", "tableEx", 800, 180, 460, 530,
                    {"Values": [col("Date", "YearMonth"), M("Operating Expense Deviation")]},
                    sort=[(M("Operating Expense Deviation"), "Descending")]))
    ni = dict(ctx["ni"])
    page.expect = ["Contra Revenue", "Net Income", money(ni[y]), "Operating Expense Deviation",
                   f"{ctx['first_spike']['dev']:.1%}"]
    # Step 9: Test 3
    b.add_tests(path)

    t = "Tutorial 14.3"
    b.check(t, "GLEntry rows", ctx["n_gl"], "COUNTROWS ( GLEntry )", 0)
    flagged = sum(c["postings"] for c in ctx["closes"])
    b.check(t, "postings flagged IsYearEndClose", flagged, "COUNTROWS ( FILTER ( GLEntry, GLEntry[IsYearEndClose] ) )", 0)
    b.check(t, "closing entries flagged", len(ctx["closes"]),
            "CALCULATE ( DISTINCTCOUNT ( GLEntry[VoucherNumber] ), GLEntry[IsYearEndClose] )", 0)
    b.check(t, "postings that found a journal entry (EntryType)", ctx["journal"],
            "COUNTROWS ( FILTER ( GLEntry, NOT ISBLANK ( GLEntry[EntryType] ) ) )", 0)
    for yr, v in ctx["ni"]:
        b.check(t, f"{yr} Net Income", round(v, 2), f"CALCULATE ( [Net Income], 'Date'[Year] = {yr} )", 0.01)
        b.check(t, f"{yr} net income with the closes (zero)", 0,
                f"CALCULATE ( SUM ( GLEntry[Credit] ) - SUM ( GLEntry[Debit] ), "
                f"Account[AccountType] IN {{ \"Revenue\", \"Expense\" }}, 'Date'[Year] = {yr} )", 0.01)
    for sub, v in ctx["sub"].items():
        b.check(t, f"{y} P&L Amount, {sub}", round(v, 2),
                f"CALCULATE ( [P&L Amount], 'Date'[Year] = {y}, Account[AccountSubType] = \"{sub}\" )", 0.01)
    for yr, v in zip(years, ctx["by_year"]):
        b.check(t, f"{yr} Operating Expense", round(v, 2), f"CALCULATE ( [Operating Expense], 'Date'[Year] = {yr} )", 0.01)
    for x in [ctx["first_spike"]] + ctx["paydays"]:
        b.check(t, f"Operating Expense Deviation {x['month']}", round(x["dev"], 6),
                f"CALCULATE ( [Operating Expense Deviation], 'Date'[YearMonth] = \"{x['month']}\" )", 0.000005)
    b.check(t, f"Expected Operating Expense {ctx['blank']} (blank)", "blank",
            f"IF ( ISBLANK ( CALCULATE ( [Expected Operating Expense], 'Date'[YearMonth] = \"{ctx['blank']}\" ) ), "
            "\"blank\", \"not blank\" )")
    spikes = {x["month"] for x in [ctx["first_spike"]] + ctx["paydays"]}
    b.check(t, "months whose deviation exceeds 20%", len(spikes),
            f"COUNTROWS ( FILTER ( VALUES ( 'Date'[YearMonth] ), [Operating Expense Deviation] > 0.2 ) )", 0)
    b.check(t, "Test 3: accounts", ctx["accounts"], TB.format("COUNTROWS ( FILTER ( Balances, NOT ISBLANK ( [Balance] ) ) )",
                                                             y=y, closes=b.data.closes_of(y)), 0)
    b.check(t, "Test 3: debit balances", round(ctx["tb"], 2),
            TB.format("SUMX ( FILTER ( Balances, [Balance] > 0 ), [Balance] )", y=y, closes=b.data.closes_of(y)), 0.01)
    b.check(t, "Test 3: credit balances", round(ctx["tb"], 2),
            TB.format("-SUMX ( FILTER ( Balances, [Balance] < 0 ), [Balance] )", y=y, closes=b.data.closes_of(y)), 0.01)


TB = ("VAR Balances = CALCULATETABLE ( ADDCOLUMNS ( VALUES ( Account[AccountID] ), \"Balance\", CALCULATE ( "
      "SUM ( GLEntry[Debit] ) - SUM ( GLEntry[Credit] ) ) ), 'Date'[Date] <= DATE ( {y}, 12, 31 ), "
      "NOT GLEntry[VoucherNumber] IN {{ \"{closes[0]}\", \"{closes[1]}\" }} ) RETURN {0}")


def back_button() -> Visual:
    """The back button Power BI adds to a page once its drill-through well holds a field."""
    return Visual("backButton", "actionButton", 20, 6, 40, 40,
                  objects={"icon": [{"properties": {"shapeType": lit("back")}, "selector": {"id": "default"}}]},
                  container_objects={"visualLink": [{"properties": {"show": lit(True), "type": lit("Back")}}]})


def drillthrough(page: Page, f: dict) -> None:
    """The field dragged into the page's Drillthrough well (Add drillthrough fields here), and the back button."""
    name = f"{page.name}Drill"
    page.page_type = "Drillthrough"
    page.extra = {"filterConfig": {"filters": [{"name": name, "field": f, "type": "Categorical",
                                                "howCreated": "Drillthrough"}]},
                  "pageBinding": {"name": f"{page.name}Binding", "type": "Drillthrough", "referenceScope": "Default",
                                  "parameters": [{"name": f"{page.name}Param", "boundFilter": name, "fieldExpr": f}]}}
    page.add(back_button())


def icon_rules(measure: dict, metadata: str, up: float, down: float) -> dict:
    """Conditional formatting > Icons, Format style Rules: an up arrow from `up`, a circle between, a down arrow at
    `down` or below, to the left of the value."""
    def cmp(kind, v):
        return {"Comparison": {"ComparisonKind": kind, "Left": measure, "Right": literal(float(v))}}
    cases = [{"Condition": cmp(2, up), "Value": literal("GreyArrowUp")},
             {"Condition": {"And": {"Left": cmp(1, down), "Right": cmp(3, up)}}, "Value": literal("CircleMedium")},
             {"Condition": cmp(4, down), "Value": literal("GreyArrowDown")}]
    return {"values": [{"properties": {"icon": {"kind": "Icon", "layout": lit("IconLeft"),
                                                "verticalAlignment": lit("Top"),
                                                "value": {"expr": {"Conditional": {"Cases": cases}}}}},
                        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": metadata}}]}


def t15_1(b: Build) -> None:
    m, y, path = b.model, b.year, CH15 / "_tutorial-01.qmd"
    ctx = ch15.t1(b.data, claim)
    # Steps 1 and 2: the promotions, related to the lines
    promo = (Query.navigator("PromotionProgram", b.xlsx, 7, "PromotionProgram")
             .select(["PromotionID", "PromotionCode", "PromotionName", "ScopeType", "DiscountPct", "EffectiveStartDate",
                      "EffectiveEndDate"]).types({"EffectiveStartDate": "type date", "EffectiveEndDate": "type date"}))
    programs = m.add(query_table(promo))
    m.relate("SalesInvoiceLine.PromotionID", "PromotionProgram.PromotionID")
    hide(m.tables["SalesInvoiceLine"], "PromotionID")
    hide(programs, "PromotionID")
    # Step 3: the Steps table the reader types (its rows read from the text), Step sorted by Order
    text = path.read_text(encoding="utf-8")
    typed = re.findall(r"`([^`]+)` and `(\d+)`", text[text.index("Type three rows"):].split("\n")[0])
    steps = m.add(entered("Steps", [("Step", "string"), ("Order", "int64")], [list(r) for r in typed]))
    steps.column("Step").sort_by = "Order"
    m.query_order.append("Steps")
    # Step 4: the measure
    m.tables[MEASURES_TABLE].measures += text_measures(path, {"Gross to Net": MONEY})
    M = lambda n: meas(MEASURES_TABLE, n)
    name = col("PromotionProgram", "PromotionName")
    # Steps 5, 6, and 8d: the Promotions page
    page = b.report.add(Page("promotions", "Promotions"))
    page.add(slicer("promotionsYear", 20, TOP, 180, 150, col("Date", "Year"), [y]))
    page.add(Visual("grossToNet", "waterfallChart", 220, TOP, 520, 400, {"Category": [col("Steps", "Step")],
                                                                        "Y": [M("Gross to Net")]},
                    title=f"Revenue from list price to net, fiscal {y}"))
    page.add(Visual("discountsByPromotion", "clusteredBarChart", 760, TOP, 500, 400,
                    {"Category": [name], "Y": [M("Discounts")]}, title="Promotional discounts by promotion",
                    filters=[keep("discountsByPromotionBlank", name, [None], exclude=True)],
                    sort=[(M("Discounts"), "Descending")],
                    container_objects={"visualTooltip": [{"properties": {
                        "show": lit(True), "type": lit("ReportPage"), "section": lit("promotionTooltip")}}]}))
    top = ctx["by_promo"][0]
    page.expect = [f"Revenue from list price to net, fiscal {y}", "Promotional discounts by promotion", typed[1][0],
                   money(ctx["revenue"]), money(ctx["list"])]
    # Step 7: the drill-through page
    detail = b.report.add(Page("promotionDetail", "Promotion Detail"))
    drillthrough(detail, name)
    detail.add(Visual("promotionTable", "tableEx", 20, TOP, 1240, 300, {"Values": [
        name, col("PromotionProgram", "ScopeType"), agg("PromotionProgram", "DiscountPct"),
        col("PromotionProgram", "EffectiveStartDate"), col("PromotionProgram", "EffectiveEndDate")]}))
    detail.add(Visual("promotionMonths", "clusteredColumnChart", 20, 370, 900, 340,
                      {"Category": [col("Date", "YearMonth")], "Y": [M("Discounts")]}))
    detail.add(card("promotionCards", 940, 370, 320, 200, [M("Invoice Lines"), M("Discounts")]))
    detail.expect = ["PromotionName", "EffectiveEndDate", top["label"], "Invoice Lines"]
    # Step 8: the tooltip page
    tip = b.report.add(Page("promotionTooltip", "Promotion Tooltip", width=320, height=240))
    tip.page_type = "Tooltip"
    tip.extra = {"pageBinding": {"name": "promotionTooltipBinding", "type": "Tooltip", "referenceScope": "Default"},
                 "objects": {"pageSize": [{"properties": {"pageSizeTypes": lit("Tooltip")}}]}}
    tip.add(Visual("tooltipMonths", "clusteredColumnChart", 0, 0, 320, 240,
                   {"Category": [col("Date", "YearMonth")], "Y": [M("Discounts")]}))
    tip.expect = ["YearMonth", "Discounts"]

    t, cy = "Tutorial 15.1", f"'Date'[Year] = {y}"
    claim(top["discounts"] > 3 * ctx["by_promo"][1]["discounts"],
          "the largest promotion gave away several times as much as any other invoiced in the year")
    claim(-ctx["step2"] > -ctx["step3"], "the price lists and overrides take far more off the list amount than the promotions")
    b.check(t, "PromotionProgram rows", ctx["promotions"], "COUNTROWS ( PromotionProgram )", 0)
    b.check(t, "invoice lines with no promotion ((Blank))", ctx["no_promo"],
            "CALCULATE ( COUNTROWS ( SalesInvoiceLine ), ISBLANK ( PromotionProgram[PromotionName] ) )", 0)
    b.check(t, "Steps rows", len(typed), "COUNTROWS ( Steps )", 0)
    for (step, _), v in zip(typed, [ctx["list"], ctx["step2"], ctx["step3"]]):
        b.check(t, f"{y} Gross to Net, {step}", round(v, 2),
                f"CALCULATE ( [Gross to Net], {cy}, Steps[Step] = \"{step}\" )", 0.01)
    b.check(t, f"{y} Gross to Net, the total column", round(ctx["revenue"], 2), f"CALCULATE ( [Gross to Net], {cy} )")
    b.check(t, f"{y} the three steps add up to revenue", round(ctx["revenue"], 2),
            f"CALCULATE ( SUMX ( VALUES ( Steps[Step] ), [Gross to Net] ), {cy} )", 0.01)
    for p_ in ctx["by_promo"]:
        b.check(t, f"{y} Discounts, promotion {p_['id']}", round(p_["discounts"], 2),
                f"CALCULATE ( [Discounts], {cy}, PromotionProgram[PromotionID] = {p_['id']} )", 0.01)
        b.check(t, f"{y} invoice lines, promotion {p_['id']}", p_["lines"],
                f"CALCULATE ( [Invoice Lines], {cy}, PromotionProgram[PromotionID] = {p_['id']} )", 0)
    for month, amount, n in ctx["top_months"]:
        b.check(t, f"promotion {top['id']} discounts {month}", round(amount, 2),
                f"CALCULATE ( [Discounts], 'Date'[YearMonth] = \"{month}\", PromotionProgram[PromotionID] = {top['id']} )",
                0.01)
    reversed_ = one("SELECT COUNT(*) FROM PromotionProgram WHERE EffectiveEndDate < EffectiveStartDate")
    b.check(t, "promotions whose end date precedes their start", reversed_,
            "COUNTROWS ( FILTER ( PromotionProgram, PromotionProgram[EffectiveEndDate] < "
            "PromotionProgram[EffectiveStartDate] ) )", 0)
    b.check(t, f"promotion {ctx['odd']['id']} end date", ctx["odd"]["end"],
            f"FORMAT ( CALCULATE ( MAX ( PromotionProgram[EffectiveEndDate] ), PromotionProgram[PromotionID] = "
            f"{ctx['odd']['id']} ), \"yyyy-mm-dd\" )")


def t15_2(b: Build) -> None:
    m, y, path = b.model, b.year, CH15 / "_tutorial-02.qmd"
    ctx = ch15.t2(b.data, claim)
    # Steps 1 and 2: the budget lines, without the balance sheet, dated, related to three dimensions
    budget = (Query.navigator("BudgetLine", b.xlsx, 77, "BudgetLine")
              .select(["BudgetLineID", "FiscalYear", "Month", "AccountID", "CostCenterID", "BudgetAmount",
                       "BudgetCategory", "DriverType"])
              .filter('([BudgetCategory] <> "Balance Sheet")'))
    budget.custom("BudgetDate", code_after(path, "name the column `BudgetDate`"), "type date")
    lines = m.add(query_table(budget))
    for many, one_ in [("BudgetLine.AccountID", "Account.AccountID"), ("BudgetLine.CostCenterID", "CostCenter.CostCenterID"),
                       ("BudgetLine.BudgetDate", "Date.Date")]:
        m.relate(many, one_)
    hide(lines, "AccountID", "CostCenterID")
    # Steps 3, 6, 7, and 9: the measures
    m.tables[MEASURES_TABLE].measures += text_measures(path, {
        "Budget": MONEY, "Actual": MONEY, "Variance": MONEY, "Variance %": "0.0%", "Flexed Budget": MONEY,
        "Variance to Flexed": MONEY, "Volume Effect": MONEY, "Classification Effect": MONEY,
        "Remaining Variance": MONEY, "Remaining %": "0.0%"})
    M = lambda n: meas(MEASURES_TABLE, n)
    opex = col("Account", "AccountSubType")
    center = col("CostCenter", "CostCenterName")
    # Steps 4, 5, 7, 9, and 10: the Budget page
    page = b.report.add(Page("budget", "Budget"))
    page.add(slicer("budgetYear", 20, TOP, 200, 150, col("Date", "Year"), [y]))
    page.add(Visual("budgetMatrix", "pivotTable", 240, TOP, 1020, 300, {"Rows": [center], "Values": [
        M("Budget"), M("Actual"), M("Variance"), M("Variance %"), M("Flexed Budget"), M("Variance to Flexed")]},
        filters=[keep("budgetMatrixOpex", opex, ["Operating Expense"])],
        objects=icon_rules(M("Variance %"), f"{MEASURES_TABLE}.Variance %", 0.05, -0.05)))
    page.add(Visual("reconciliation", "tableEx", 20, 370, 800, 340, {"Values": [
        center, M("Variance"), M("Volume Effect"), M("Classification Effect"), M("Remaining Variance"),
        M("Remaining %")]}, filters=[keep("reconciliationOpex", opex, ["Operating Expense"])]))
    ytd = (dax_blocks(path, "skip")[0])
    ((ytd_name, ytd_expr),) = definitions(ytd)
    page.add(Visual("varianceByMonth", "tableEx", 840, 370, 420, 340, {"Values": [
        col("Date", "YearMonth"), M("Variance to Flexed"),
        {"NativeVisualCalculation": {"Language": "dax", "Expression": ytd_expr, "Name": ytd_name}}]},
        filters=[keep("varianceByMonthYear", col("Date", "Year"), [y]), keep("varianceByMonthOpex", opex,
                                                                           ["Operating Expense"])]))
    centers = {c["name"]: c for c in ctx["centers"]}
    page.expect = ["Variance to Flexed", "Gray up arrow", "Gray down arrow", "Yellow circle", ytd_name,
                   money(ctx["opex"])] + [money(ctx["ytd"][i]) for i in (0, 5, 6, 11)]
    # Step 8: the drill-through page
    detail = b.report.add(Page("costCenterDetail", "Cost Center Detail"))
    drillthrough(detail, center)
    levels = [col("Account", "AccountNumber"), col("Account", "AccountName")]
    detail.add(Visual("accountMatrix", "pivotTable", 20, TOP, 1240, 640, {
        "Rows": levels, "Values": [M("Budget"), M("Actual"), M("Variance")]},
        filters=[keep("accountMatrixOpex", opex, ["Operating Expense"])],
        extra={"expansionStates": [{"roles": ["Rows"], "levels": [
            {"queryRefs": ["Account.AccountNumber"], "isCollapsed": False, "identityKeys": [levels[0]], "isPinned": True},
            {"queryRefs": ["Account.AccountName"], "isCollapsed": True, "isPinned": True}]}]}, active=("Rows",)))
    first_account = one("SELECT MIN(a.AccountNumber) FROM BudgetLine b JOIN Account a ON a.AccountID = b.AccountID "
                        "WHERE a.AccountSubType = 'Operating Expense'")
    detail.expect = ["AccountNumber", "Back", f"Expanded {first_account}"]
    # Step 11: Test 4
    b.add_tests(path)

    t, cy = "Tutorial 15.2", f"'Date'[Year] = {y}"
    ox = "Account[AccountSubType] = \"Operating Expense\""
    b.check(t, "BudgetLine rows (Balance Sheet cleared)",
            one("SELECT COUNT(*) FROM BudgetLine WHERE BudgetCategory <> 'Balance Sheet'"), "COUNTROWS ( BudgetLine )", 0)
    b.check(t, "budget lines with no BudgetDate row", 0,
            "COUNTROWS ( FILTER ( BudgetLine, ISBLANK ( RELATED ( 'Date'[Year] ) ) ) )", 0)
    b.check(t, f"Test 4: {y} operating expense Budget", round(ctx["opex"], 2), f"CALCULATE ( [Budget], {cy}, {ox} )", 0.01)
    b.check(t, f"Test 4: {y} Flexed Budget", round(ctx["flexed_total"], 2),
            f"CALCULATE ( [Flexed Budget], {cy}, {ox} )", 0.01)
    b.check(t, f"Test 4: {y} Actual", round(ctx["actual"], 2), f"CALCULATE ( [Actual], {cy}, {ox} )", 0.01)
    for name, c in centers.items():
        where = "ISBLANK ( CostCenter[CostCenterName] )" if name == "(Blank)" else f"CostCenter[CostCenterName] = \"{name}\""
        b.check(t, f"{name}: Budget", round(c["budget"], 2), f"CALCULATE ( [Budget], {cy}, {ox}, {where} )", 0.01)
        b.check(t, f"{name}: Actual", round(c["actual"], 2), f"CALCULATE ( [Actual], {cy}, {ox}, {where} )", 0.01)
        b.check(t, f"{name}: Variance %", round(c["pct"], 6), f"CALCULATE ( [Variance %], {cy}, {ox}, {where} )",
                0.000005)
        b.check(t, f"{name}: Flexed Budget", round(c["flexed"], 2),
                f"CALCULATE ( [Flexed Budget], {cy}, {ox}, {where} )", 0.01)
        b.check(t, f"{name}: Classification Effect", round(c["cls"], 2),
                f"CALCULATE ( [Classification Effect], {cy}, {ox}, {where} )", 0.01)
        b.check(t, f"{name}: Remaining Variance", round(c["remaining"], 2),
                f"CALCULATE ( [Remaining Variance], {cy}, {ox}, {where} )", 0.01)
    flagged = sorted(n for n, c in centers.items() if abs(c["pct"]) >= 0.05)
    b.check(t, "cost centers whose variance is 5% of budget or more", len(flagged),
            f"CALCULATE ( COUNTROWS ( FILTER ( VALUES ( CostCenter[CostCenterName] ), ABS ( [Variance %] ) >= 0.05 ) ), "
            f"{cy}, {ox} )", 0)
    claim(len(flagged) == 3, "three cost centers stand out")
    b.check(t, f"{y} Volume Effect", round(ctx["volume"], 2), f"CALCULATE ( [Volume Effect], {cy}, {ox} )", 0.01)
    b.check(t, f"{y} Classification Effect, all cost centers (zero)", 0,
            f"CALCULATE ( [Classification Effect], {cy}, {ox} )", 0.01)
    b.check(t, f"{y} flexed commission (Chapter 7)", round(ctx["flexed_com"], 2),
            f"CALCULATE ( [Flexed Budget], {cy}, Account[AccountNumber] = 6290 )", 0.01)
    for i, (mon, v) in enumerate(ctx["months"]):
        ym = f"{y}-{i + 1:02d}"
        b.check(t, f"Variance to Flexed {ym}", round(v, 2),
                f"CALCULATE ( [Variance to Flexed], 'Date'[YearMonth] = \"{ym}\", {ox} )", 0.01)
    for i in (5, 6, 11):                         # the year to date the visual calculation shows in June, July, December
        b.check(t, f"{ytd_name} through {y}-{i + 1:02d}", round(ctx["ytd"][i], 2),
                f"CALCULATE ( [Variance to Flexed], DATESBETWEEN ( 'Date'[Date], DATE ( {y}, 1, 1 ), "
                f"EOMONTH ( DATE ( {y}, {i + 1}, 1 ), 0 ) ), {ox} )", 0.01)


def t15_3(b: Build) -> None:
    m, y, path = b.model, b.year, CH15 / "_tutorial-03.qmd"
    ctx = ch15.t3(b.data, claim)
    # Steps 1 to 3: the plant's Tables, the columns kept, the headers merged into the facts
    labor = (Query.navigator("LaborTimeEntry", b.xlsx, 60, "LaborTimeEntry")
             .select(["LaborTimeEntryID", "EmployeeID", "WorkOrderOperationID", "WorkDate", "LaborType", "RegularHours",
                      "OvertimeHours", "ExtendedLaborCost"]).types({"WorkDate": "type date"}))
    ops = Query.navigator("WorkOrderOperation", b.xlsx, 52, "WorkOrderOperation").select(
        ["WorkOrderOperationID", "WorkCenterID"])
    comp = (Query.navigator("ProductionCompletion", b.xlsx, 56, "ProductionCompletion")
            .select(["ProductionCompletionID", "CompletionDate"]).types({"CompletionDate": "type date"}))
    comp_lines = Query.navigator("ProductionCompletionLine", b.xlsx, 57, "ProductionCompletionLine").select(
        ["ProductionCompletionLineID", "ProductionCompletionID", "ItemID", "QuantityCompleted"])
    employee = Query.navigator("Employee", b.xlsx, 74, "Employee").select(
        ["EmployeeID", "EmployeeName", "JobTitle", "PayClass"])
    center = Query.navigator("WorkCenter", b.xlsx, 47, "WorkCenter").select(
        ["WorkCenterID", "WorkCenterCode", "WorkCenterName"])
    labor.merge(ops, "WorkOrderOperationID", "WorkOrderOperationID", ["WorkCenterID"])
    comp_lines.merge(comp, "ProductionCompletionID", "ProductionCompletionID", ["CompletionDate"])
    m.stage(ops)
    m.stage(comp)
    labor_t = m.add(query_table(labor))
    comp_t = m.add(query_table(comp_lines))
    m.add(query_table(employee))
    m.add(query_table(center))
    item = m.tables["Item"]
    rechoose(item.query, ["StandardLaborHoursPerUnit"], b.xlsx, "Item")
    sync(item)
    # Step 4: the relationships, the keys hidden
    for many, one_ in [("LaborTimeEntry.EmployeeID", "Employee.EmployeeID"),
                       ("LaborTimeEntry.WorkCenterID", "WorkCenter.WorkCenterID"), ("LaborTimeEntry.WorkDate", "Date.Date"),
                       ("ProductionCompletionLine.ItemID", "Item.ItemID"),
                       ("ProductionCompletionLine.CompletionDate", "Date.Date")]:
        m.relate(many, one_)
    hide(labor_t, "LaborTimeEntryID", "EmployeeID", "WorkOrderOperationID", "WorkCenterID")
    hide(comp_t, "ProductionCompletionLineID", "ProductionCompletionID", "ItemID")
    # Steps 5, 6, 7, 10, and 11: the measures
    hours = "#,0"
    m.tables[MEASURES_TABLE].measures += text_measures(path, {
        "Manufacturing Hours": hours, "Direct Hours": hours, "Indirect Hours": hours, "Overtime Hours": hours,
        "Standard Hours": hours, "Standard Hours to Cut-off": hours, "Hours per Standard Hour": "0.00",
        "Hours per Standard Hour TTM": "0.00", "Hours per Standard Hour 2024": "0.00", "Overtime Share": "0.0%"})
    M = lambda n: meas(MEASURES_TABLE, n)
    years = [y - 2, y - 1, y]
    year = col("Date", "Year")
    # Steps 7 to 11: the Plant page (the comparison table of Steps 8 and 9 is deleted in Step 10)
    page = b.report.add(Page("plant", "Plant"))
    page.add(card("plantCards", 20, TOP, 600, 110, [M("Hours per Standard Hour TTM"), M("Hours per Standard Hour 2024")],
                  filters=[keep("plantCardsYears", year, years)]))
    page.add(Visual("ttmLine", "lineChart", 20, 176, 600, 250, {"Category": [col("Date", "YearMonth")],
                                                              "Y": [M("Hours per Standard Hour TTM")]},
                    filters=[keep("ttmLineYears", year, years)]))
    page.add(Visual("directByCenter", "clusteredBarChart", 640, TOP, 620, 370,
                    {"Category": [col("WorkCenter", "WorkCenterName")], "Y": [M("Direct Hours")]},
                    filters=[keep("directByCenterYear", year, [y])]))
    titles = [t_ for t_, _, _ in ctx["titles"]]
    page.add(Visual("overtimeShare", "clusteredColumnChart", 20, 436, 1240, 274, {
        "Category": [col("Employee", "JobTitle")], "Series": [year], "Y": [M("Overtime Share")]},
        filters=[keep("overtimeShareYears", year, years), keep("overtimeShareTitles", col("Employee", "JobTitle"), titles)]))
    page.expect = ["Hours per Standard Hour TTM", f"{ctx['card']:.2f}", f"{ctx['first']:.2f}",
                   center_name(ctx["centers"][0][0]), titles[0]]
    # Step 12: the About page with a page navigator, first; the detail pages hidden; a navigator on every visible page
    about = b.report.add(Page("about", "About"), before="salesDiscounts")
    last = ctx["last"]
    about.add(textbox("aboutText", 20, TOP, 1240, 300, [
        ("Charles River Reports", True),
        "Purpose: a monthly reporting package on sales and discounts, operating expense against budget, and the plant's "
        "hours, each with its comparison and its detail.",
        "Readers: the sales manager (Promotions), the department managers (Budget), and the production manager (Plant).",
        "Source: CharlesRiver.xlsx, refreshed through Power Query. Period: fiscal years "
        f"{years[0]} to {y}; the time records end on {last}, because the last pay periods are still open.",
        f"Definitions: every KPI is a measure of the {MEASURES_TABLE} table, with its description; the trailing hours per "
        "standard hour is Hours per Standard Hour TTM.",
        "Checks: the Validation page reconciles the model to the control totals, and the Tests tab in DAX query view "
        "tests the measures."], size=12))
    for p_ in b.report.pages:
        if p_.name in ("promotionDetail", "promotionTooltip", "costCenterDetail"):
            p_.hidden = True
        elif p_.name != "notes":
            if p_.name == "validation":                  # moved down to make room for the navigator
                for v in p_.visuals:
                    v.y += TOP - 20
            p_.add(Visual("pageNavigator", "pageNavigator", 20, 4, 1240, 44, objects={"pages": [{"properties": {
                "showHiddenPages": lit(False), "showTooltipPages": lit(False)}}]}))
    about.visuals[-1].y, about.visuals[-1].h = TOP + 320, 60        # on the About page, the navigator below the text
    about.expect = ["Charles River Reports", "Sales and Discounts", "Plant"]
    b.report.active = "about"
    # Step 13: Test 5
    b.add_tests(path)

    t = "Tutorial 15.3"
    for kind, n in ctx["types"]:
        b.check(t, f"LaborTimeEntry rows, {kind}", n,
                f"CALCULATE ( COUNTROWS ( LaborTimeEntry ), LaborTimeEntry[LaborType] = \"{labor_type(kind)}\" )", 0)
    b.check(t, "last WorkDate", last, "FORMAT ( MAX ( LaborTimeEntry[WorkDate] ), \"yyyy-mm-dd\" )")
    b.check(t, "direct lines with a work center", ctx["matched"],
            "CALCULATE ( COUNTROWS ( LaborTimeEntry ), LaborTimeEntry[LaborType] = \"Direct Manufacturing\", "
            "NOT ISBLANK ( LaborTimeEntry[WorkCenterID] ) )", 0)
    b.check(t, "ProductionCompletionLine rows", ctx["completions"], "COUNTROWS ( ProductionCompletionLine )", 0)
    b.check(t, "completion lines with no item", 0,
            "COUNTROWS ( FILTER ( ProductionCompletionLine, ISBLANK ( RELATED ( 'Item'[StandardLaborHoursPerUnit] ) ) ) )", 0)
    for x in ctx["tests"]:
        cy = f"'Date'[Year] = {x['year']}"
        b.check(t, f"Test 5: {x['year']} Manufacturing Hours", round(x["hours"], 2),
                f"CALCULATE ( [Manufacturing Hours], {cy} )", 0.01)
        b.check(t, f"Test 5: {x['year']} Standard Hours to Cut-off", round(x["standard"], 2),
                f"CALCULATE ( [Standard Hours to Cut-off], {cy} )", 0.01)
        b.check(t, f"Test 5: {x['year']} Hours per Standard Hour", round(x["ratio"], 6),
                f"CALCULATE ( [Hours per Standard Hour], {cy} )", 0.000005)
    direct = sum(h for _, h in ctx["centers"]) + ctx["blank"]
    b.check(t, f"{y} Direct Hours (KEEPFILTERS keeps them direct)", round(direct, 2),
            f"CALCULATE ( [Direct Hours], 'Date'[Year] = {y} )", 0.01)
    b.check(t, f"{y} Direct Hours plus Indirect Hours equal Manufacturing Hours", 0,
            f"CALCULATE ( [Direct Hours] + [Indirect Hours] - [Manufacturing Hours], 'Date'[Year] = {y} )", 0.01)
    for name, h in ctx["centers"]:
        b.check(t, f"{y} Direct Hours, {name}", round(h, 2),
                f"CALCULATE ( [Direct Hours], 'Date'[Year] = {y}, WorkCenter[WorkCenterName] = \"{center_name(name)}\" )",
                0.01)
    b.check(t, f"{y} Direct Hours, (Blank) work center", round(ctx["blank"], 2),
            f"CALCULATE ( [Direct Hours], 'Date'[Year] = {y}, ISBLANK ( WorkCenter[WorkCenterName] ) )", 0.01)
    series = dict(ctx["ttm"])
    peak = max(series, key=series.get)
    for ym in sorted({f"{yr}-12" for yr in years} | {peak}):
        b.check(t, f"Hours per Standard Hour TTM {ym}", round(series[ym], 6),
                f"CALCULATE ( [Hours per Standard Hour TTM], 'Date'[YearMonth] = \"{ym}\" )", 0.000005)
    b.check(t, f"TTM before a full window ({years[0]}-11, blank)", "blank",
            f"IF ( ISBLANK ( CALCULATE ( [Hours per Standard Hour TTM], 'Date'[YearMonth] = \"{years[0]}-11\" ) ), "
            "\"blank\", \"not blank\" )")
    b.check(t, "the card's TTM, filtered to the three years", round(ctx["card"], 6),
            f"CALCULATE ( [Hours per Standard Hour TTM], 'Date'[Year] IN {{ {', '.join(map(str, years))} }} )", 0.000005)
    b.check(t, "the card without a year filter (blank)", "blank",
            "IF ( ISBLANK ( [Hours per Standard Hour TTM] ), \"blank\", \"not blank\" )")
    b.check(t, "Hours per Standard Hour 2024", round(ctx["first"], 6), "[Hours per Standard Hour 2024]", 0.000005)
    for title, first, current in ctx["titles"]:
        for yr, v in ((years[0], first), (y, current)):
            b.check(t, f"Overtime Share {title} {yr}", round(v, 6),
                    f"CALCULATE ( [Overtime Share], 'Date'[Year] = {yr}, Employee[JobTitle] = \"{title}\" )", 0.000005)
    for yr, v in zip(years, ctx["plant"]):
        b.check(t, f"Overtime Share, plant, {yr}", round(v, 6), f"CALCULATE ( [Overtime Share], 'Date'[Year] = {yr} )",
                0.000005)


def labor_type(kind: str) -> str:
    """The LaborType value of a kind the notes shorten (Direct, Indirect, NonManufacturing)."""
    return kind if kind == "NonManufacturing" else f"{kind} Manufacturing"


def center_name(short: str) -> str:
    """The WorkCenterName of a work center the notes shorten (Packing -> Packing Work Center)."""
    return f"{short} Work Center"


def md_table(path: Path, label: str) -> list[list[str]]:
    """The body rows of the Markdown table captioned {#label}, cells without their code backticks."""
    lines = path.read_text(encoding="utf-8").split("\n")
    i = next(i for i, l in enumerate(lines) if "{#" + label + "}" in l) - 1
    while not lines[i].strip():
        i -= 1
    body = []
    while lines[i].startswith("|"):
        body.insert(0, lines[i])
        i -= 1
    return [[c.strip().strip("`") for c in r.strip().strip("|").split("|")] for r in body][2:]


def ta_1(b: Build) -> None:
    m, y, path = b.model, b.year, APPX / "_tutorial-01.qmd"
    ctx = appendix_a.t1(b.data, claim)
    # Step 1 builds the access review in Audit Monitoring.pbix (the chapter 16 chain), not in this file.
    # Step 2: each employee's cost center
    employee = m.tables["Employee"]
    rechoose(employee.query, ["CostCenterID"], b.xlsx, "Employee")
    sync(employee)
    # Step 3: the security table the reader types (tbl-a-02 without its Cost center column), hidden
    rows_ = md_table(path, "tbl-a-02")
    security = m.add(entered("Security", [("UserPrincipalName", "string"), ("CostCenterID", "int64")],
                             [[u, c] for u, c, _ in rows_], hidden=True))
    for c in security.columns:
        c.hidden = True
    m.query_order.append("Security")
    # Steps 5 and 6: the roles, with the rules as the text prints them
    rule_cc, rule_item, rule_security = (" ".join(r.split()) for r in dax_blocks(path, "skip"))
    m.roles += [Role("Cost Center Managers", {"CostCenter": rule_cc, "Employee": rule_cc, "Item": rule_item,
                                              "Security": rule_security}),
                Role("Finance")]
    # Step 9: the two measures and their cards
    m.tables[MEASURES_TABLE].measures += text_measures(path, {"Cost Centers Shown": None, "Who Am I": None})
    M = lambda n: meas(MEASURES_TABLE, n)
    shown = "Cost centers shown"
    b.report.page("budget").add(card("costCentersShown", 20, 216, 200, 140, [M("Cost Centers Shown")], title=shown))
    b.report.page("incomeStatement").add(card("costCentersShown", 1040, TOP, 220, 110, [M("Cost Centers Shown")],
                                              title=shown))
    b.report.page("about").add(card("whoAmI", 20, TOP + 390, 600, 100, [M("Who Am I")]))
    names = sorted(r[0] for r in rows("SELECT DISTINCT CostCenterName FROM CostCenter"))
    for page in ("budget", "incomeStatement"):
        b.report.page(page).expect.append(shown)
    b.report.page("about").expect.append("Who Am I")

    t, cy, ox = "Guided Tutorial A.1", f"'Date'[Year] = {y}", "Account[AccountSubType] = \"Operating Expense\""
    blank = lambda expr: f"IF ( ISBLANK ( {expr} ), \"blank\", \"not blank\" )"
    b.check(t, "employees with a cost center",
            one("SELECT COUNT(*) FROM Employee WHERE CostCenterID IS NOT NULL"),
            "COUNTROWS ( FILTER ( Employee, NOT ISBLANK ( Employee[CostCenterID] ) ) )", 0)
    b.check(t, "Security rows", len(rows_), "COUNTROWS ( Security )", 0)
    b.check(t, "Security cost centers that exist", len(rows_),
            "COUNTROWS ( FILTER ( Security, NOT ISBLANK ( LOOKUPVALUE ( CostCenter[CostCenterName], "
            "CostCenter[CostCenterID], Security[CostCenterID] ) ) ) )", 0)
    b.check(t, "Cost Centers Shown without a role (all of them)", ", ".join(names), "[Cost Centers Shown]")
    b.check(t, "Who Am I without a role (your own sign-in)", "not blank", blank("[Who Am I]"))

    def as_user(upn: str, expr: str) -> str:
        """`expr` with the role's rules applied for a literal user name (the rules' text, USERPRINCIPALNAME replaced)."""
        cc, item = (r.replace("USERPRINCIPALNAME ()", f"\"{upn}\"") for r in (rule_cc, rule_item))
        return (f"CALCULATE ( {expr}, FILTER ( ALL ( CostCenter ), {cc} ), FILTER ( ALL ( Employee ), {cc} ), "
                f"FILTER ( ALL ( 'Item' ), {item} ) )")

    for who, v in (("Sales Manager", ctx["s"]), ("Warehouse Manager", ctx["w"]), ("Production Manager", ctx["p"])):
        upn, label = v["upn"], f"as {v['upn'].split('@')[0]} ({who})"
        b.check(t, f"{label}: Cost Centers Shown", ", ".join(sorted(v["centers"])),
                as_user(upn, "[Cost Centers Shown]"))
        if v["budget"]:
            b.check(t, f"{label}: {y} operating expense Budget", round(v["budget"], 2),
                    as_user(upn, f"CALCULATE ( [Budget], {cy}, {ox} )"), 0.01)
            b.check(t, f"{label}: {y} Actual", round(v["actual"], 2),
                    as_user(upn, f"CALCULATE ( [Actual], {cy}, {ox} )"), 0.01)
            b.check(t, f"{label}: {y} Flexed Budget", round(v["flexed"], 2),
                    as_user(upn, f"CALCULATE ( [Flexed Budget], {cy}, {ox} )"), 0.01)
        else:
            b.check(t, f"{label}: {y} operating expense Budget (an empty Budget page)", "blank",
                    blank(as_user(upn, f"CALCULATE ( [Budget], {cy}, {ox} )")))
        b.check(t, f"{label}: {y} Net Income", round(v["ni"], 2), as_user(upn, f"CALCULATE ( [Net Income], {cy} )"), 0.01)
        b.check(t, f"{label}: {y} Revenue (every sale)", round(ctx["revenue"], 2),
                as_user(upn, f"CALCULATE ( [Revenue], {cy} )"), 0.01)
        if v["hours"]:
            b.check(t, f"{label}: {y} Manufacturing Hours", round(v["hours"], 2),
                    as_user(upn, f"CALCULATE ( [Manufacturing Hours], {cy} )"), 0.01)
            b.check(t, f"{label}: {y} Hours per Standard Hour", round(v["ratio"], 6),
                    as_user(upn, f"CALCULATE ( [Hours per Standard Hour], {cy} )"), 0.000005)
        else:
            b.check(t, f"{label}: {y} Manufacturing Hours (an empty Plant page)", "blank",
                    blank(as_user(upn, f"CALCULATE ( [Manufacturing Hours], {cy} )")))
        b.check(t, f"{label}: employees", v["employees"], as_user(upn, "COUNTROWS ( Employee )"), 0)
    former = f"{ctx['former']}@charlesriver.example"
    b.check(t, f"as {ctx['former']} (not in the security table): Revenue", "blank",
            blank(as_user(former, f"CALCULATE ( [Revenue], {cy} )")))
    b.check(t, f"as {ctx['former']}: cost centers", 0, as_user(former, "COUNTROWS ( CostCenter )"), 0)
    b.check(t, f"as {ctx['former']}: Cost Centers Shown", "blank", blank(as_user(former, "[Cost Centers Shown]")))
    b.check(t, f"as {ctx['former']}: customers (Customer has no rule)", ctx["customers"],
            as_user(former, "COUNTROWS ( Customer )"), 0)
    b.check(t, f"{y} Net Income without a role", round(ctx["company"], 2), f"CALCULATE ( [Net Income], {cy} )", 0.01)
    claim(ctx["s"]["ni"] > 2 * ctx["company"], "the Sales Manager's net income is more than twice the company's")
    claim(ctx["w"]["ni"] < 0, "the Warehouse Manager's income statement is a loss")

    # The real roles, run by the engine on a connection that applies them: with the Windows sign-in, which the
    # security table does not list, Cost Center Managers shows nothing (deny by default); Finance shows everything.
    deny = [("Guided Tutorial A.1", c) for c in [
        Check("cost centers visible", 0, "COUNTROWS ( CostCenter )", 0),
        Check("items visible", 0, "COUNTROWS ( 'Item' )", 0),
        Check("employees visible", 0, "COUNTROWS ( Employee )", 0),
        Check("security rows visible", 0, "COUNTROWS ( Security )", 0),
        Check(f"{y} Revenue", "blank", blank(f"CALCULATE ( [Revenue], {cy} )")),
        Check("Cost Centers Shown", "blank", blank("[Cost Centers Shown]")),
        Check("customers visible (Customer has no rule)", ctx["customers"], "COUNTROWS ( Customer )", 0),
        Check("Who Am I (the sign-in the rules compare)", "not blank", blank("[Who Am I]"))]]
    full = [("Guided Tutorial A.1", c) for c in [
        Check("cost centers visible", len(names), "COUNTROWS ( CostCenter )", 0),
        Check(f"{y} Revenue", round(ctx["revenue"], 2), f"CALCULATE ( [Revenue], {cy} )"),
        Check(f"{y} Net Income", round(ctx["company"], 2), f"CALCULATE ( [Net Income], {cy} )", 0.01),
        Check("Cost Centers Shown", ", ".join(names), "[Cost Centers Shown]")]]
    b.role_checks = {"Cost Center Managers, Windows sign-in": ("Cost Center Managers", None, deny),
                     "Finance": ("Finance", None, full)}


TUTORIALS = [("13.1", t13_1), ("13.2", t13_2), ("13.3", t13_3), ("14.1", t14_1), ("14.2", t14_2), ("14.3", t14_3),
             ("15.1", t15_1), ("15.2", t15_2), ("15.3", t15_3), ("A.1", ta_1)]
