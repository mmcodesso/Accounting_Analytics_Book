"""Power Query M text with the step names the Power Query Editor gives the reader's own steps.

A query imported through the Navigator reads Source, Navigation, Changed Type. Changed Type holds the types Power
Query detects from the first 200 rows of the Table (Microsoft Learn, "Data types in Power Query"); `detected_types`
reproduces that detection from the dataset, and `corrections` applies what a tutorial tells the reader to change with
Replace current, which edits the Changed Type step itself.
"""

from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

PREV = "{prev}"     # stands for the previous step in a step expression (replaced, not str.format)


def m_string(text: str) -> str:
    return '"' + text.replace('"', '""') + '"'


def step(name: str) -> str:
    """A step name as M writes it: plain when it is an identifier, #"..." otherwise."""
    return name if name.replace("_", "").isalnum() and not name[0].isdigit() else f'#"{name}"'


@lru_cache(maxsize=None)
def detected_types(xlsx: Path, sheet: str) -> tuple[tuple[str, str], ...]:
    """The types Power Query detects for each column of a CharlesRiver.xlsx Table from its first 200 rows, read from
    the workbook itself (a date cell reads as datetime; a date typed as text stays text)."""
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    rows = wb[sheet].iter_rows(min_row=1, max_row=201, values_only=True)
    header = list(next(rows))
    head = list(rows)
    wb.close()
    out = []
    for i, col in enumerate(header):
        values = [row[i] for row in head if row[i] is not None]
        if not values:
            kind = "type any"
        elif all(isinstance(v, datetime) for v in values):
            kind = "type datetime"
        elif all(isinstance(v, bool) for v in values):
            kind = "type logical"
        elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            kind = "Int64.Type" if all(float(v).is_integer() for v in values) else "type number"
        elif all(isinstance(v, str) for v in values):
            kind = "type text"
        else:
            kind = "type any"
        out.append((col, kind))
    return tuple(out)


def type_list(pairs: list[tuple[str, str]]) -> str:
    return "{" + ", ".join("{" + f"{m_string(c)}, {t}" + "}" for c, t in pairs) + "}"


def navigator_query(path: str, table_number: int, table: str, types: list[tuple[str, str]],
                    corrections: dict[str, str] | None = None, extra: list[tuple[str, str]] = ()) -> str:
    """Source, Navigation, Changed Type (with any Replace current corrections), then the extra steps in order.

    `extra` holds (step name, expression with {prev} for the previous step's name)."""
    nav = f"T{table_number}_{table}_Table"
    fixed = [(c, (corrections or {}).get(c, t)) for c, t in types]
    lines = [f"    Source = Excel.Workbook(File.Contents({m_string(path)}), null, true),",
             f"    {nav} = Source{{[Item={m_string(f'T{table_number}_{table}')},Kind=\"Table\"]}}[Data],",
             f"    #\"Changed Type\" = Table.TransformColumnTypes({nav},{type_list(fixed)})"]
    prev = '#"Changed Type"'
    for name, expr in extra:
        lines[-1] += ","
        lines.append(f"    {step(name)} = {expr.replace(PREV, prev)}")
        prev = step(name)
    return "let\n" + "\n".join(lines) + f"\nin\n    {prev}"


def steps_query(steps: list[tuple[str, str]]) -> str:
    """A query written as (step name, expression with {prev}) pairs; the first expression has no {prev}."""
    lines, prev = [], None
    for name, expr in steps:
        lines.append(f"    {step(name)} = {expr.replace(PREV, prev) if prev else expr}")
        prev = step(name)
    return "let\n" + ",\n".join(lines) + f"\nin\n    {prev}"


def select_columns(columns: list[str]) -> str:
    return "Table.SelectColumns({prev}," + "{" + ", ".join(m_string(c) for c in columns) + "})"


def transform_types(pairs: list[tuple[str, str]]) -> str:
    return "Table.TransformColumnTypes({prev}," + type_list(pairs) + ")"


def merge(right: str, left_key: str, right_key: str, new_column: str) -> str:
    return (f"Table.NestedJoin({PREV}, {{{m_string(left_key)}}}, {right}, {{{m_string(right_key)}}}, "
            f"{m_string(new_column)}, JoinKind.LeftOuter)")


def expand(column: str, fields: list[str]) -> str:
    names = "{" + ", ".join(m_string(f) for f in fields) + "}"
    return f"Table.ExpandTableColumn({PREV}, {m_string(column)}, {names}, {names})"


def add_custom(name: str, formula: str) -> str:
    return f"Table.AddColumn({PREV}, {m_string(name)}, each {formula})"


def today() -> str:
    return date.today().isoformat()


def merge_keys(right: str, keys: list[str], new_column: str) -> str:
    """A left outer merge on several key columns, matched in order (Ctrl+click in the Merge dialog)."""
    names = "{" + ", ".join(m_string(k) for k in keys) + "}"
    return f"Table.NestedJoin({PREV}, {names}, {right}, {names}, {m_string(new_column)}, JoinKind.LeftOuter)"


def rename(pairs: list[tuple[str, str]]) -> str:
    return "Table.RenameColumns({prev},{" + ", ".join("{" + f"{m_string(a)}, {m_string(b)}" + "}" for a, b in pairs) + "})"


def select_rows(condition: str) -> str:
    return f"Table.SelectRows({PREV}, each {condition})"
