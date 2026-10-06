"""Report pages and visuals of a Power BI companion project, written as PBIR and validated against Microsoft's schemas.

Field wells are the visual's data roles: cardVisual Data; card, tableEx and slicer Values; clusteredBarChart,
clusteredColumnChart and lineChart Category, Y, Series; lineClusteredColumnComboChart Category, Y (columns), Y2 (line);
pivotTable Rows, Columns, Values; waterfallChart Category, Breakdown, Y. A field is a column, a measure, or an
aggregation of a column (the implicit "Sum of LineTotal" a reader gets by dragging a numeric column into a well).
The schemas come from github.com/microsoft/json-schemas, fetched once and cached in pbibuild/schemas.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMAS = HERE / "schemas"
BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
VC = f"{BASE}/visualContainer/2.12.0/schema.json"
PAGE = f"{BASE}/page/2.1.0/schema.json"
PAGES = f"{BASE}/pagesMetadata/1.1.0/schema.json"
AGG = {"sum": 0, "avg": 1, "count": 5, "distinctcount": 2, "min": 3, "max": 4}   # QueryAggregateFunction


def _registry():
    from referencing import Registry, Resource

    def retrieve(uri: str):
        import urllib.request
        rel = uri.split("/json-schemas/", 1)[1]
        local = SCHEMAS / rel
        if not local.exists():
            local.parent.mkdir(parents=True, exist_ok=True)
            raw = "https://raw.githubusercontent.com/microsoft/json-schemas/main/" + rel
            local.write_bytes(urllib.request.urlopen(raw, timeout=60).read())
        return Resource.from_contents(json.loads(local.read_text(encoding="utf-8")))
    return Registry(retrieve=retrieve)


_REG = None


def validate(doc: dict) -> None:
    global _REG
    import jsonschema
    _REG = _REG or _registry()
    schema = _REG.get_or_retrieve(doc["$schema"]).value.contents
    jsonschema.Draft7Validator(schema, registry=_REG).validate(doc)


# --- fields ---------------------------------------------------------------------------------------------------------

def col(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas(entity: str, prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def agg(entity: str, prop: str, function: str = "sum") -> dict:
    return {"Aggregation": {"Expression": col(entity, prop), "Function": AGG[function]}}


def _ref(f: dict) -> tuple[str, str, str]:
    """(entity, property, the name Desktop shows) of a field."""
    if "NativeVisualCalculation" in f:                # a visual calculation: Desktop's queryRef is "select"
        return None, "select", f["NativeVisualCalculation"]["Name"]
    if "Aggregation" in f:
        inner = f["Aggregation"]["Expression"]["Column"]
        fn = {v: k for k, v in AGG.items()}[f["Aggregation"]["Function"]]
        label = {"sum": "Sum", "avg": "Average", "count": "Count", "distinctcount": "Count", "min": "Min",
                 "max": "Max"}[fn]
        e, p = inner["Expression"]["SourceRef"]["Entity"], inner["Property"]
        func = {"sum": "Sum", "avg": "Avg", "count": "CountNonNull", "distinctcount": "CountNonNull", "min": "Min",
                "max": "Max"}[fn]
        return e, f"{func}({e}.{p})", f"{label} of {p}"
    kind = next(iter(f))
    e, p = f[kind]["Expression"]["SourceRef"]["Entity"], f[kind]["Property"]
    return e, f"{e}.{p}", p


def projection(f: dict, display: str | None = None) -> dict:
    _, query_ref, native = _ref(f)
    p = {"field": f, "queryRef": query_ref, "nativeQueryRef": native}
    if display:
        p["displayName"] = display
    return p


def lit(value) -> dict:
    if isinstance(value, bool):
        return {"expr": {"Literal": {"Value": "true" if value else "false"}}}
    if isinstance(value, (int, float)):
        return {"expr": {"Literal": {"Value": f"{value}D"}}}
    return {"expr": {"Literal": {"Value": "'" + str(value).replace("'", "''") + "'"}}}


# --- visuals and pages ----------------------------------------------------------------------------------------------

@dataclass
class Visual:
    name: str
    vtype: str
    x: float
    y: float
    w: float
    h: float
    roles: dict = field(default_factory=dict)      # role -> [field or (field, display name)]
    title: str | None = None
    objects: dict | None = None
    container_objects: dict | None = None
    filters: list | None = None
    sort: list | None = None                       # [(field, "Ascending"|"Descending")]
    alt_text: str | None = None
    hidden: bool = False
    extra: dict | None = None                      # other visual properties (expansionStates, ...)
    active: tuple = ()                             # roles whose levels are all shown (a matrix's Rows): active

    def doc(self, z: int) -> dict:
        v: dict = {"visualType": self.vtype, "drillFilterOtherVisuals": True}
        if self.extra:
            v.update(self.extra)
        if self.roles:
            state = {}
            for role, fields in self.roles.items():
                state[role] = {"projections": [projection(*f) if isinstance(f, tuple) else projection(f)
                                               for f in fields]}
                if role in self.active:            # without it, an expanded matrix row shows no children
                    for p in state[role]["projections"]:
                        p["active"] = True
            v["query"] = {"queryState": state}
            if self.sort:
                v["query"]["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in self.sort],
                                                "isDefaultSort": False}
        if self.objects:
            v["objects"] = self.objects
        cont = dict(self.container_objects or {})
        if self.title:
            cont["title"] = [{"properties": {"show": lit(True), "text": lit(self.title)}}]
        if self.alt_text:
            cont["general"] = [{"properties": {"altText": lit(self.alt_text)}}]
        if cont:
            v["visualContainerObjects"] = cont
        d = {"$schema": VC, "name": self.name,
             "position": {"x": self.x, "y": self.y, "z": z, "height": self.h, "width": self.w, "tabOrder": z},
             "visual": v}
        if self.filters:
            d["filterConfig"] = {"filters": self.filters}
        if self.hidden:
            d["isHidden"] = True
        return d


def textbox(name: str, x, y, w, h, paragraphs: list, size: int = 11) -> Visual:
    """A text box; each paragraph is a string or (string, bold)."""
    paras = []
    for p in paragraphs:
        text, bold = (p, False) if isinstance(p, str) else p
        style = {"fontSize": f"{size}pt"}
        if bold:
            style["fontWeight"] = "bold"
        paras.append({"textRuns": [{"value": text, "textStyle": style}]})
    return Visual(name, "textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": paras}}]})


@dataclass
class Page:
    name: str
    display: str
    visuals: list[Visual] = field(default_factory=list)
    hidden: bool = False
    width: int = 1280
    height: int = 720
    page_type: str | None = None                   # "Tooltip" for a tooltip page
    extra: dict | None = None                      # other page.json properties (drillthrough config, filters)
    expect: list[str] = field(default_factory=list)  # text the canvas must show once rendered (verification only)

    def add(self, v: Visual) -> Visual:
        assert all(x.name != v.name for x in self.visuals), f"{self.name}: duplicate visual {v.name}"
        self.visuals.append(v)
        return v

    def doc(self) -> dict:
        d = {"$schema": PAGE, "name": self.name, "displayName": self.display, "displayOption": "FitToPage",
             "height": self.height, "width": self.width}
        if self.hidden:
            d["visibility"] = "HiddenInViewMode"
        if self.page_type:
            d["type"] = self.page_type
        if self.extra:
            d.update(self.extra)
        return d


@dataclass
class Report:
    pages: list[Page] = field(default_factory=list)
    active: str | None = None

    def page(self, name: str) -> Page:
        return next(p for p in self.pages if p.name == name)

    def add(self, p: Page, before: str | None = None) -> Page:
        assert all(x.name != p.name for x in self.pages), f"duplicate page {p.name}"
        if before:
            self.pages.insert(next(i for i, x in enumerate(self.pages) if x.name == before), p)
        else:
            self.pages.append(p)
        return p

    def write(self, folder: Path) -> None:
        pages = folder / "definition" / "pages"
        if pages.exists():
            shutil.rmtree(pages)
        for p in self.pages:
            pd = p.doc()
            validate(pd)
            _write(pages / p.name / "page.json", pd)
            for z, v in enumerate(p.visuals):
                vd = v.doc(z * 1000)
                validate(vd)
                _write(pages / p.name / "visuals" / v.name / "visual.json", vd)
        meta = {"$schema": PAGES, "pageOrder": [p.name for p in self.pages],
                "activePageName": self.active or self.pages[0].name}
        validate(meta)
        _write(pages / "pages.json", meta)


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
