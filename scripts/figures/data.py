"""Read-only access to the Charles River database for the figure generator.

Relationship endpoints are never drawn by hand: cardinality() and trace_card()
compute them from the rows, and the edge carries an er= or trace= style key so
check_figures.py can recompute and compare them later.
"""

from __future__ import annotations

import sqlite3
import os
import sys
from functools import lru_cache
from pathlib import Path

from drawio import AMBER, CROSS_WIDTH, GRAY, Diagram

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from shared.calculations.foundations import relationship
DB_PATH = (Path(os.environ.get("CHARLESRIVER_DATA", REPO_ROOT / "datasets"))
           / "CharlesRiver.sqlite").resolve()


@lru_cache(maxsize=1)
def connection() -> sqlite3.Connection:
    if not DB_PATH.is_file():
        raise SystemExit(f"Dataset not found: {DB_PATH}. Put it in datasets/ or set CHARLESRIVER_DATA.")
    return sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)


def q(sql: str, *args) -> list[tuple]:
    return connection().execute(sql, args).fetchall()


def one(sql: str, *args) -> tuple:
    rows = q(sql, *args)
    if len(rows) != 1:
        raise ValueError(f"Expected one row, got {len(rows)}: {sql} {args}")
    return rows[0]


def require_columns(table: str, columns: list[str]) -> None:
    """Fail loudly if a figure names a table or column that the database does not have."""
    actual = {row[1] for row in q(f"PRAGMA table_info({table})")}
    if not actual:
        raise ValueError(f"Table {table} does not exist in the database")
    missing = [c for c in columns if c not in actual]
    if missing:
        raise ValueError(f"{table} has no column(s) {', '.join(missing)}")


def _child_end(minimum: int, maximum: int) -> str:
    if minimum == 0:
        return "ERzeroToOne" if maximum <= 1 else "ERzeroToMany"
    return "ERmandOne" if maximum == 1 else "ERoneToMany"


def cardinality(parent: str, pk: str, child: str, fk: str) -> tuple[str, str]:
    """Return the (parent end, child end) Draw.io ER markers implied by the data."""
    return relationship(connection(), parent, pk, child, fk)


def trace_card(source: str, pk: str) -> tuple[str, str]:
    """Markers for the source-document trace from a source table to its GLEntry rows."""
    orphans = q(
        f"SELECT COUNT(*) FROM GLEntry g WHERE SourceDocumentType = ? AND NOT EXISTS "
        f"(SELECT 1 FROM {source} t WHERE t.{pk} = g.SourceDocumentID)", source
    )[0][0]
    minimum, maximum = q(
        f"SELECT MIN(COALESCE(x.c, 0)), MAX(COALESCE(x.c, 0)) FROM {source} p LEFT JOIN "
        f"(SELECT SourceDocumentID AS k, COUNT(*) AS c FROM GLEntry WHERE SourceDocumentType = ? "
        f"GROUP BY 1) x ON x.k = p.{pk}", source
    )[0]
    return ("ERzeroToOne" if orphans else "ERmandOne"), _child_end(minimum, maximum)


def relate(d: Diagram, parent: str, pk: str, child: str, fk: str, src: str, tgt: str,
           color: str = GRAY, **kwargs) -> str:
    """Draw parent -> child with data-true endpoints. src is on the parent, tgt on the child."""
    start, end = cardinality(parent, pk, child, fk)
    if color == AMBER:
        kwargs.setdefault("width", CROSS_WIDTH)
    return d.edge(src, tgt, start=start, end=end, color=color,
                  meta=f"er={parent}.{pk}>{child}.{fk};", **kwargs)


def trace(d: Diagram, source: str, pk: str, src: str, tgt: str, **kwargs) -> str:
    """Draw the dashed source-document trace from a source table to GLEntry."""
    start, end = trace_card(source, pk)
    return d.edge(src, tgt, start=start, end=end, color=AMBER, dashed=True,
                  meta=f"trace={source}.{pk};", **kwargs)
