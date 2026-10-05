"""The semantic model of a Power BI companion project, written as TMDL.

A `Query` holds a Power Query query as the reader builds it in the Power Query Editor, with the editor's step names
(Source, Navigation, Changed Type, Removed Other Columns, Filtered Rows, Added Custom, Merged Queries, Expanded ...),
and tracks every column's type through the steps, so that the same definition gives the M text and the model's
column list (Desktop rejects a model whose columns do not match its query). Changed Type holds the types Power Query
detects from the first 200 rows of the Excel Table (xlbuild.pq.detected_types), with the corrections a tutorial tells
the reader to make with Replace current.

A `Model` holds the loaded tables (query tables, calculated tables, the Enter data tables), the queries that only feed
others (Enable load cleared: shared expressions), relationships, measures, and roles, and writes the TMDL folder.
"""

from __future__ import annotations

import base64
import json
import uuid
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from xlbuild import pq

T = "\t"
TMDL_TYPE = {"Int64.Type": "int64", "type number": "double", "type text": "string", "type date": "dateTime",
             "type datetime": "dateTime", "type logical": "boolean", "type any": "string",
             "Currency.Type": "decimal", "Percentage.Type": "double"}
DATE_FORMAT = "Short Date"
MEASURES_TABLE = "Key Measures"


def quote(name: str) -> str:
    """A TMDL object name, quoted when it holds anything but letters, digits, and underscores."""
    return name if name.replace("_", "").isalnum() and not name[0].isdigit() else "'" + name.replace("'", "''") + "'"


class Query:
    """A Power Query query with its steps and its output columns (name -> M type)."""

    def __init__(self, name: str):
        self.name = name
        self.steps: list[tuple[str, str]] = []
        self.columns: dict[str, str] = {}
        self._counts: dict[str, int] = {}

    def _step(self, base: str, expr: str) -> None:
        n = self._counts.get(base, 0)
        self._counts[base] = n + 1
        self.steps.append((base if n == 0 else f"{base}{n}", expr))

    @classmethod
    def navigator(cls, name: str, xlsx: Path, number: int, table: str, corrections: dict | None = None) -> "Query":
        """Source, Navigation, and Changed Type, as the Navigator's Transform Data creates them."""
        q = cls(name)
        types = [(c, (corrections or {}).get(c, t)) for c, t in pq.detected_types(xlsx, table)]
        q.columns = dict(types)
        q.source = ("navigator", number, table, types)
        q._counts["Changed Type"] = 1
        return q

    @classmethod
    def reference(cls, name: str, of: "Query") -> "Query":
        """A query started with Reference on another query."""
        q = cls(name)
        q.columns = dict(of.columns)
        q.source = ("reference", of.name)
        return q

    def select(self, columns: list[str]) -> "Query":
        missing = [c for c in columns if c not in self.columns]
        assert not missing, f"{self.name}: no columns {missing}"
        self._step("Removed Other Columns", pq.select_columns(columns))
        self.columns = {c: self.columns[c] for c in self.columns if c in columns}
        return self

    def filter(self, condition: str) -> "Query":
        self._step("Filtered Rows", pq.select_rows(condition))
        return self

    def types(self, pairs: dict[str, str]) -> "Query":
        self._step("Changed Type", pq.transform_types(list(pairs.items())))
        self.columns.update(pairs)
        return self

    def custom(self, column: str, formula: str, mtype: str = "type any") -> "Query":
        self._step("Added Custom", pq.add_custom(column, formula))
        self.columns[column] = "type any"
        if mtype != "type any":
            self.types({column: mtype})
        return self

    def merge(self, other: "Query", left: str | list[str], right: str | list[str], fields: list[str]) -> "Query":
        """Merge Queries (left outer) and expand the fields without the prefix."""
        lk, rk = ([left] if isinstance(left, str) else left), ([right] if isinstance(right, str) else right)
        lst = lambda ks: "{" + ", ".join(pq.m_string(k) for k in ks) + "}"
        self._step("Merged Queries", f"Table.NestedJoin({pq.PREV}, {lst(lk)}, {pq.step(other.name)}, {lst(rk)}, "
                                     f"{pq.m_string(other.name)}, JoinKind.LeftOuter)")
        self._step(f"Expanded {other.name}", pq.expand(other.name, fields))
        for f in fields:
            self.columns[f] = other.columns[f]
        return self

    def rename(self, pairs: dict[str, str]) -> "Query":
        self._step("Renamed Columns", pq.rename(list(pairs.items())))
        self.columns = {pairs.get(c, c): t for c, t in self.columns.items()}
        return self

    def raw(self, step: str, expr: str, columns: dict[str, str] | None = None) -> "Query":
        """Any other step, with the output columns it leaves (None: unchanged)."""
        self._step(step, expr)
        if columns is not None:
            self.columns = columns
        return self

    def m(self, path: str) -> str:
        kind = self.source[0]
        if kind == "navigator":
            _, number, table, types = self.source
            return pq.navigator_query(path, number, table, types, None, self.steps)
        return pq.steps_query([("Source", pq.step(self.source[1]))] + self.steps)


@dataclass
class Column:
    name: str
    dtype: str
    source: str | None = None             # sourceColumn (a calculated table's "[Name]")
    fmt: str | None = None
    summarize: str = "none"
    hidden: bool = False
    sort_by: str | None = None
    expression: str | None = None         # a DAX calculated column
    extra: tuple = ()

    def tmdl(self) -> str:
        if self.expression:
            head = f"{T}column {quote(self.name)} = {self.expression}"
        else:
            head = f"{T}column {quote(self.name)}"
        lines = [head, f"{T*2}dataType: {self.dtype}"]
        if self.fmt:
            lines.append(f"{T*2}formatString: {self.fmt}")
        if self.hidden:
            lines.append(f"{T*2}isHidden")
        lines.append(f"{T*2}summarizeBy: {self.summarize}")
        if not self.expression:
            lines.append(f"{T*2}sourceColumn: {self.source or self.name}")
        if self.sort_by:
            lines.append(f"{T*2}sortByColumn: {quote(self.sort_by)}")
        lines += [f"{T*2}{e}" for e in self.extra]
        return "\n".join(lines) + "\n"


@dataclass
class Measure:
    name: str
    dax: str
    fmt: str | None = None
    description: str | None = None
    hidden: bool = False
    display_folder: str | None = None     # a display folder of its table (an exercise's measures: "Ex 14.1")

    def tmdl(self) -> str:
        out = [f"{T}/// {self.description}"] if self.description else []
        dax = self.dax.strip("\n")
        if "\n" in dax:
            out.append(f"{T}measure {quote(self.name)} =")
            out += [T * 3 + line for line in dax.split("\n")]
        else:
            out.append(f"{T}measure {quote(self.name)} = {dax}")
        if self.fmt:
            out.append(f"{T*2}formatString: {self.fmt}")
        if self.hidden:
            out.append(f"{T*2}isHidden")
        if self.display_folder:
            out.append(f"{T*2}displayFolder: {self.display_folder}")
        return "\n".join(out) + "\n"


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    query: Query | None = None            # an import partition from a Power Query query
    dax: str | None = None                # a calculated table
    entered: list[list] | None = None     # an Enter data table: rows (the columns are self.columns)
    hidden: bool = False
    props: tuple = ()

    def column(self, name: str) -> Column:
        return next(c for c in self.columns if c.name == name)

    def tmdl(self, path: str) -> str:
        out = [f"table {quote(self.name)}"] + ([f"{T}isHidden"] if self.hidden else []) + [f"{T}{p}" for p in self.props]
        out.append("")
        out += [m.tmdl() for m in self.measures]
        out += [c.tmdl() for c in self.columns]
        if self.query is not None:
            body = "\n".join(T * 3 + line if line else "" for line in self.query.m(path).split("\n"))
            out.append(f"{T}partition {quote(self.name)} = m\n{T*2}mode: import\n{T*2}source =\n{body}\n")
        elif self.dax is not None:
            body = "\n".join(T * 3 + line for line in self.dax.strip("\n").split("\n"))
            out.append(f"{T}partition {quote(self.name)} = calculated\n{T*2}mode: import\n{T*2}source =\n{body}\n")
        elif self.entered is not None:
            out.append(f"{T}partition {quote(self.name)} = m\n{T*2}mode: import\n{T*2}source =\n"
                       + "\n".join(T * 3 + line for line in entered_m(self).split("\n")) + "\n")
        return "\n".join(out) + "\n"


def entered_m(table: Table) -> str:
    """The M that Home > Enter data writes: the rows as compressed JSON, then the column types."""
    raw = json.dumps(table.entered, separators=(",", ":")).encode("utf-8")
    packed = zlib.compressobj(9, zlib.DEFLATED, -15)
    text = base64.b64encode(packed.compress(raw) + packed.flush()).decode("ascii")
    names = ", ".join(f"{c.name} = _t" for c in table.columns)
    m_types = {"int64": "Int64.Type", "double": "type number", "string": "type text", "dateTime": "type date",
               "boolean": "type logical", "decimal": "Currency.Type"}
    typed = ", ".join("{" + f"{pq.m_string(c.name)}, {m_types[c.dtype]}" + "}" for c in table.columns)
    return ("let\n"
            f'    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("{text}", '
            f'BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) '
            f"in type table [{names}]),\n"
            f'    #"Changed Type" = Table.TransformColumnTypes(Source,{{{typed}}})\n'
            'in\n    #"Changed Type"')


def query_table(q: Query, formats: dict[str, str] | None = None, hidden: set[str] = frozenset(),
                summarize: dict[str, str] | None = None, sort_by: dict[str, str] | None = None) -> Table:
    """A loaded query as a model table: one column per query column, typed as Power Query types it. Numbers are
    summarized by Sum, as Desktop sets them, unless `summarize` says otherwise (a key, code, or year: none)."""
    cols = []
    for name, mtype in q.columns.items():
        dtype = TMDL_TYPE[mtype]
        default = "sum" if dtype in ("int64", "double", "decimal") else "none"
        fmt = (formats or {}).get(name) or (DATE_FORMAT if mtype in ("type date",) else None)
        cols.append(Column(name, dtype, fmt=fmt, summarize=(summarize or {}).get(name, default),
                           hidden=name in hidden, sort_by=(sort_by or {}).get(name)))
    return Table(q.name, cols, query=q)


@dataclass
class Relationship:
    from_column: str                      # Table.Column on the many side
    to_column: str                        # Table.Column on the one side
    active: bool = True
    both: bool = False

    def tmdl(self, model_name: str) -> str:
        rid = uuid.uuid5(uuid.NAMESPACE_URL, f"{model_name}/{self.from_column}/{self.to_column}")
        ft, fc = self.from_column.split(".", 1)
        tt, tc = self.to_column.split(".", 1)
        lines = [f"relationship {rid}", f"{T}fromColumn: {quote(ft)}.{quote(fc)}", f"{T}toColumn: {quote(tt)}.{quote(tc)}"]
        if not self.active:
            lines.append(f"{T}isActive: false")
        if self.both:
            lines.append(f"{T}crossFilteringBehavior: bothDirections")
        return "\n".join(lines) + "\n"


@dataclass
class Role:
    name: str
    filters: dict[str, str] = field(default_factory=dict)   # table -> DAX filter
    model_permission: str = "read"

    def tmdl(self) -> str:
        out = [f"role {quote(self.name)}", f"{T}modelPermission: {self.model_permission}", ""]
        for table, dax in self.filters.items():
            out.append(f"{T}tablePermission {quote(table)} = {dax}")
            out.append("")
        return "\n".join(out) + "\n"


@dataclass
class Model:
    name: str
    tables: dict[str, Table] = field(default_factory=dict)
    staging: dict[str, Query] = field(default_factory=dict)      # Enable load cleared
    relationships: list[Relationship] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    query_order: list[str] = field(default_factory=list)

    def add(self, table: Table) -> Table:
        self.tables[table.name] = table
        if table.query is not None and table.name not in self.query_order:
            self.query_order.append(table.name)
        return table

    def stage(self, q: Query) -> Query:
        self.staging[q.name] = q
        if q.name not in self.query_order:
            self.query_order.append(q.name)
        return q

    def relate(self, many: str, one: str, active: bool = True, both: bool = False) -> None:
        self.relationships.append(Relationship(many, one, active, both))

    def measure_host(self, measure: str) -> str:
        for t in self.tables.values():
            if any(m.name == measure for m in t.measures):
                return t.name
        raise KeyError(f"no measure {measure}")

    def write(self, folder: Path, path: str) -> None:
        d = folder / "definition"
        write(d / "database.tmdl", f"database {quote(self.name)}\n{T}compatibilityLevel: 1601\n")
        order = json.dumps(self.query_order, separators=(",", ":"))
        write(d / "model.tmdl", "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
                                "\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n"
                                "\t\treturnErrorValuesAsNull\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n\n"
                                f"annotation PBI_QueryOrder = {order}\n")
        if self.staging:
            parts = []
            for q in self.staging.values():
                body = "\n".join(T * 2 + line if line else "" for line in q.m(path).split("\n"))
                parts.append(f"expression {quote(q.name)} =\n{body}\n{T}annotation PBI_ResultType = Table\n")
            write(d / "expressions.tmdl", "\n".join(parts))
        if self.relationships:
            write(d / "relationships.tmdl", "\n".join(r.tmdl(self.name) for r in self.relationships))
        for t in self.tables.values():
            write(d / "tables" / f"{t.name}.tmdl", t.tmdl(path))
        for r in self.roles:
            write(d / "roles" / f"{r.name}.tmdl", r.tmdl())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
