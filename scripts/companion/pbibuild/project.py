"""A Power BI project (PBIP) on disk: the .pbip file, the semantic model (TMDL, DAX query tabs), and the report (PBIR).

The Notes page is the Power BI counterpart of the Excel Solution Notes worksheet: the file, the dataset release, what
the file holds, the steps completed, and what the results mean, as text boxes. Its checks live in a DAX query tab named
Checks, which returns one row per check with the expected value, the actual value from the model, and whether they
agree, so a reader can rerun it in DAX query view after a refresh; the builder runs the same query in Desktop.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from pbibuild.model import Model, write
from pbibuild.pbir import Page, Report, textbox

NOTES_PAGE = "notes"


@dataclass
class Check:
    label: str
    expected: float | int | str
    dax: str                              # a scalar DAX expression
    tolerance: float = 0.005


def dax_literal(v) -> str:
    if isinstance(v, str):
        return '"' + v.replace('"', '""') + '"'
    if isinstance(v, bool):
        return "TRUE ()" if v else "FALSE ()"
    return repr(float(v)) if isinstance(v, float) else str(v)


def checks_query(checks: list[tuple[str, Check]]) -> str:
    """One DAX query that returns every check: section, check, expected, actual, agrees."""
    rows = []
    for section, c in checks:
        exp = dax_literal(c.expected)
        agrees = (f"( {c.dax} ) = {exp}" if isinstance(c.expected, str)
                  else f"ABS ( ( {c.dax} ) - {exp} ) <= {c.tolerance}")
        rows.append(f'    ROW ( "Section", "{section}", "Check", "{c.label}", "Expected", {exp}, "Actual", {c.dax}, '
                    f'"Agrees", {agrees} )')
    head = ("// Every check of this companion file: the expected value, the actual value from the model, and whether\n"
            "// they agree. Refresh the model first (Home > Refresh), then choose Run.\n")
    if len(rows) == 1:
        return head + "EVALUATE\n" + rows[0].strip() + "\n"
    return head + "EVALUATE\nUNION (\n" + ",\n".join(rows) + "\n)\n"


@dataclass
class Project:
    name: str                             # the file name without .pbip, e.g. "Charles River Reports"
    model: Model
    report: Report
    queries: dict[str, str] = field(default_factory=dict)        # DAX query tabs: name -> query text
    checks: list[tuple[str, Check]] = field(default_factory=list)
    tmdl_scripts: dict[str, str] = field(default_factory=dict)   # TMDL view script tabs: name -> script text

    def check(self, section: str, label: str, expected, dax: str, tolerance: float = 0.005) -> None:
        # Date and Item are reserved words: an unquoted one breaks the whole Checks query
        bad = re.search(r"(?<!['\[])\b(Date|Item)\b(?=\s*[\[)])", dax)
        assert not bad, f"{label}: write '{bad.group(1)}' in quotes: {dax}"
        self.checks.append((section, Check(label, expected, dax, tolerance)))

    def notes_page(self, stamp: dict, role: str, sections: list[dict], contents: dict[str, list[str]]) -> None:
        """(Re)write the Notes page: the last page of the report, as the Solution Notes worksheet is in Excel."""
        self.report.pages = [p for p in self.report.pages if p.name != NOTES_PAGE]
        page = Page(NOTES_PAGE, "Notes", width=1280, height=2000)
        left = [("Notes", True), f"{self.name}.pbip: {role}", "",
                ("About this file", True), f"Book: {stamp['book']}", f"Dataset: {stamp['dataset']}",
                f"Source: {stamp['source']}", f"Built: {stamp['built']}", "",
                ("What the file holds", True)] + [f"{k}: " + ("; ".join(v) if v else "none") for k, v in contents.items()]
        left += ["", ("Checks", True),
                 "Every check below is in the DAX query tab Checks: open DAX query view, select the Checks tab, and "
                 "choose Run after a refresh. Each row gives the expected value, the actual value, and whether they "
                 "agree."] + [f"{s}: {c.label}: {c.expected:,.2f}" if isinstance(c.expected, float) else
                              f"{s}: {c.label}: {c.expected}" for s, c in self.checks]
        right = [("Steps completed and what they mean", True)]
        for sec in sections:
            right += ["", (f"{sec['label']}: {sec['title']}", True)] + sec["items"]
            if sec.get("meaning"):
                right += [f"What it means: {sec['meaning']}"]
        page.add(textbox("notesLeft", 20, 20, 610, 1960, left, size=10))
        page.add(textbox("notesRight", 650, 20, 610, 1960, right, size=10))
        self.report.add(page)
        self.queries["Checks"] = checks_query(self.checks)

    def write(self, folder: Path, source_path: str) -> Path:
        """Write the project into `folder`; queries read `source_path`. Returns the .pbip path."""
        if folder.exists():
            import shutil
            shutil.rmtree(folder)
        sm, rp = folder / f"{self.name}.SemanticModel", folder / f"{self.name}.Report"
        pbip = folder / f"{self.name}.pbip"
        write(pbip, json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0", "artifacts": [{"report": {"path": f"{self.name}.Report"}}],
            "settings": {"enableAutoRecovery": True}}, indent=2))
        write(sm / "definition.pbism", json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.2", "settings": {}}, indent=2))
        self.model.write(sm, source_path)
        if self.queries:
            for tab, text in self.queries.items():
                write(sm / "DAXQueries" / f"{tab}.dax", text)
            write(sm / ".pbi" / "daxQueries.json", json.dumps({
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/daxQueries/1.0.0/schema.json",
                "version": "1.0.0", "tabOrder": list(self.queries), "defaultTab": next(iter(self.queries))}, indent=2))
        if self.tmdl_scripts:                 # each tab a .tmdl file in TMDLScripts, its settings in .pbi (Learn)
            for tab, text in self.tmdl_scripts.items():
                write(sm / "TMDLScripts" / f"{tab}.tmdl", text)
            write(sm / ".pbi" / "tmdlScripts.json", json.dumps({
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/tmdlScripts/1.0.0/schema.json",
                "version": "1.0.0", "tabOrder": list(self.tmdl_scripts), "defaultTab": next(iter(self.tmdl_scripts))},
                indent=2))
        write(rp / "definition.pbir", json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0", "datasetReference": {"byPath": {"path": f"../{self.name}.SemanticModel"}}}, indent=2))
        write(rp / "definition" / "version.json", json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0"}, indent=2))
        write(rp / "definition" / "report.json", json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
            "themeCollection": {"baseTheme": {"name": "CY26SU09", "reportVersionAtImport": {
                "visual": "2.12.0", "page": "2.1.0", "report": "3.3.0"}, "type": "SharedResources"}}}, indent=2))
        self.report.write(rp)
        # Desktop cannot open a project with a path of 260 characters or more (it waits forever for the model)
        longest = max((str(p.resolve()) for p in folder.rglob("*") if p.is_file()), key=len)
        assert len(longest) < 250, f"path too long for Power BI Desktop ({len(longest)} characters): {longest}"
        return pbip
