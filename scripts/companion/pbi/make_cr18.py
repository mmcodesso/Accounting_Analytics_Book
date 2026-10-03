"""Write the Chapter 18 reference model, CR18, as a Power BI project (PBIP): the item costs of the workbook's Costs
sheet (from ch18_twins.py), the invoice lines with their invoice dates, and the two disconnected tables of
Requirement 5, Costing View and Item Rank. The measures are defined in the test queries (cr18_checks.dax)."""
import json
import uuid
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paths import REFERENCE_MODELS, XLSX as _XLSX  # noqa: E402

HERE = REFERENCE_MODELS  # ch18_twins.py writes the two CSVs here
OUT = REFERENCE_MODELS / "ch18_ref"
NAME = "CR18"
T = "\t"


def csv_m(path, types):
    t = ", ".join(f'{{"{c}", {ty}}}' for c, ty in types)
    return f"""let
    Source = Csv.Document(File.Contents("{path}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{{t}}}, "en-US")
in
    Typed"""


def column(name, dtype, fmt=None, summarize="none", source=None):
    lines = [f"{T}column {name}", f"{T*2}dataType: {dtype}"]
    if fmt:
        lines.append(f"{T*2}formatString: {fmt}")
    lines += [f"{T*2}summarizeBy: {summarize}", f"{T*2}sourceColumn: {source or name}"]
    return "\n".join(lines) + "\n"


def calc_column(name, dtype, source):
    return f"{T}column {name}\n{T*2}dataType: {dtype}\n{T*2}isNameInferred\n{T*2}summarizeBy: none\n{T*2}sourceColumn: [{source}]\n"


def table(name, columns, m=None, dax=None):
    q = f"'{name}'" if " " in name else name
    out = [f"table {q}", ""] + columns
    if m:
        body = "\n".join(T * 3 + line for line in m.split("\n"))
        out.append(f"{T}partition {q} = m\n{T*2}mode: import\n{T*2}source =\n{body}\n")
    if dax:
        body = "\n".join(T * 3 + line for line in dax.strip("\n").split("\n"))
        out.append(f"{T}partition {q} = calculated\n{T*2}mode: import\n{T*2}source =\n{body}\n")
    return "\n".join(out) + "\n"


ic = str(HERE / "cr18_itemcosts.csv")
sl = str(HERE / "cr18_sales.csv")
tables = {
    "ItemCosts": table("ItemCosts", [
        column("ItemID", "int64"), column("ItemCode", "string"), column("Family", "string"), column("ItemGroup", "string"),
        column("SupplyMode", "string"), column("StandardCost", "double", "#,0.00"), column("AbsorptionCost", "double", "#,0.00"),
        column("TimeDrivenCost", "double", "#,0.00")],
        m=csv_m(ic, [("ItemID", "Int64.Type"), ("ItemCode", "type text"), ("Family", "type text"), ("ItemGroup", "type text"),
                     ("SupplyMode", "type text"), ("StandardCost", "type number"), ("AbsorptionCost", "type number"),
                     ("TimeDrivenCost", "type number")])),
    "SalesInvoiceLine": table("SalesInvoiceLine", [
        column("SalesInvoiceLineID", "int64"), column("ItemID", "int64"), column("InvoiceDate", "dateTime", "Short Date"),
        column("Quantity", "double", summarize="sum"), column("LineTotal", "double", "#,0.00", summarize="sum"),
        column("Year", "int64")],
        m=csv_m(sl, [("SalesInvoiceLineID", "Int64.Type"), ("ItemID", "Int64.Type"), ("InvoiceDate", "type date"),
                     ("Quantity", "type number"), ("LineTotal", "type number")]).replace(
            '"en-US")\nin\n    Typed', '"en-US"),\n    WithYear = Table.AddColumn(Typed, "Year", each Date.Year([InvoiceDate]), Int64.Type)\nin\n    WithYear')),
    "Costing View": table("Costing View", [calc_column("View", "string", "View"), calc_column("Order", "int64", "Order")],
                          dax='DATATABLE ( "View", STRING, "Order", INTEGER, { { "Standard", 1 }, { "Absorption", 2 }, { "Time-driven", 3 } } )'),
    "Item Rank": table("Item Rank", [calc_column("Rank", "int64", "Rank")],
                       dax='SELECTCOLUMNS ( GENERATESERIES ( 1, 250, 1 ), "Rank", [Value] )'),
}
relationships = f"relationship {uuid.uuid5(uuid.NAMESPACE_URL, "CR18/SalesInvoiceLine.ItemID/ItemCosts.ItemID")}\n{T}fromColumn: SalesInvoiceLine.ItemID\n{T}toColumn: ItemCosts.ItemID\n"
model = f"""model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: powerBI_V3
	sourceQueryCulture: en-US
	dataAccessOptions
		legacyRedirects
		returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_QueryOrder = {json.dumps(["ItemCosts", "SalesInvoiceLine"])}
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


sm = OUT / f"{NAME}.SemanticModel"
rp = OUT / f"{NAME}.Report"
write(OUT / f"{NAME}.pbip", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
write(sm / "definition.pbism", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2", "settings": {}}, indent=2))
write(sm / "definition" / "database.tmdl", f"database {NAME}\n\tcompatibilityLevel: 1601\n")
write(sm / "definition" / "model.tmdl", model)
write(sm / "definition" / "relationships.tmdl", relationships)
for n, text in tables.items():
    write(sm / "definition" / "tables" / f"{n}.tmdl", text)
write(rp / "definition.pbir", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
write(rp / "definition" / "version.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "version": "2.0.0"}, indent=2))
write(rp / "definition" / "report.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY26SU09", "reportVersionAtImport": {
        "visual": "2.12.0", "page": "2.1.0", "report": "3.3.0"}, "type": "SharedResources"}}}, indent=2))
write(rp / "definition" / "pages" / "pages.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": ["families"], "activePageName": "families"}, indent=2))
write(rp / "definition" / "pages" / "families" / "page.json", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": "families", "displayName": "Families", "displayOption": "FitToPage", "height": 720, "width": 1280}, indent=2))
print("wrote", OUT)
