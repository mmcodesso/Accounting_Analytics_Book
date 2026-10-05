"""SQL solution scripts (instructor files): one script per exercise (`Ex 9.1.sql`), or one per case or capstone
(`Case.sql`, `MakeBuy.sql`, `Credits.sql`), in the book's script standard.

A script opens with the header comment of Tutorial 9.3 (purpose, database, preparer and date, checks). Each query sits
under two comment lines, what it does or tests and its population and expected result, as the audit library of
Chapter 12 and the capstones ask, and ends with the result of a read-only run (`-- Result: N rows`). A closing notes
block repeats the exercise's requirements and instructor note and lists the checks.

A chapter module (`sqlbuild/ex09.py`, ...) lists `EXERCISES = [("9.1", fn), ...]`; each function receives the build
`b` and adds queries to a script with `b.script(...)`. A check compares a value computed independently (the notes'
context functions in `facts/notes`, or read-only SQL of the module's own) with a value read from the query's result,
so a script that runs but answers wrongly fails the build.
"""

from __future__ import annotations

import sqlite3
import textwrap
from dataclasses import dataclass, field
from typing import Callable

WIDTH = 110                  # the notes block's line width
MAX_SQL_LINE = 90            # the book keeps query lines under about 70 characters; this is the hard limit


@dataclass
class Result:
    """What a query returned: column names and rows."""
    columns: list[str]
    rows: list[tuple]

    def __len__(self) -> int:
        return len(self.rows)

    def col(self, name: str) -> list:
        i = self.columns.index(name)
        return [r[i] for r in self.rows]

    def cell(self, row: int, name: str):
        return self.rows[row][self.columns.index(name)]

    def value(self, name: str | None = None):
        """The single value of a one-row result (its only column, or the named one)."""
        assert len(self.rows) == 1, f"expected one row, got {len(self.rows)}"
        return self.rows[0][0] if name is None else self.cell(0, name)

    def where(self, **match) -> dict:
        """The one row whose columns equal the given values, as a dict."""
        hits = [r for r in self.rows if all(r[self.columns.index(k)] == v for k, v in match.items())]
        assert len(hits) == 1, f"expected one row with {match}, got {len(hits)}"
        return dict(zip(self.columns, hits[0]))

    def total(self, name: str) -> float:
        return sum(v or 0 for v in self.col(name))


@dataclass
class Check:
    label: str
    expected: object                         # computed independently of the query
    actual: Callable[[Result], object]       # read from the query's result
    tolerance: float = 0.005

    def agrees(self, result: Result) -> tuple[bool, object]:
        got = self.actual(result)
        if isinstance(self.expected, (int, float)) and not isinstance(self.expected, bool) and got is not None:
            return abs(float(got) - float(self.expected)) <= self.tolerance, got
        return got == self.expected, got


@dataclass
class Query:
    what: str                                # first comment line: what the query does or tests
    population: str                          # second line: its population and expected result
    sql: str
    checks: list[Check] = field(default_factory=list)
    section: str = ""                        # the exercise or requirement it answers


@dataclass
class Script:
    file: str                                # "Ex 9.1.sql"
    title: str                               # the header's first line after the file name
    checks_line: str                         # the header's Checks line
    database: str = "CharlesRiver_Work.sqlite (a copy of CharlesRiver.sqlite)"
    queries: list[Query] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    answers: list[tuple[str, str]] = field(default_factory=list)   # (label, text): written answers, after the queries

    def answer(self, label: str, text: str) -> None:
        """A written answer (a memo, an explanation) built from computed values, printed after the queries as a
        comment block headed "Model answer (<label>)"; paragraphs are separated by blank lines."""
        self.answers.append((label, text))

    def query(self, what: str, population: str, sql: str, checks: list[Check] = (), section: str = "") -> Query:
        q = Query(what, population, textwrap.dedent(sql).strip("\n"), list(checks), section)
        assert q.sql.rstrip().endswith(";"), f"{self.file}: a query must end with a semicolon: {what}"
        long = [line for line in q.sql.split("\n") if len(line) > MAX_SQL_LINE]
        assert not long, f"{self.file}: lines longer than {MAX_SQL_LINE} characters: {long[:2]}"
        for line in (what, population):
            assert "\n" not in line and not line.startswith("--"), f"{self.file}: write comments without '--'"
        self.queries.append(q)
        return q

    def header(self, prepared: str) -> str:
        return (f"/* {self.file}: {self.title}\n   Database: {self.database}\n   Prepared by: {prepared}\n"
                f"   Checks: {self.checks_line} */")

    def text(self, prepared: str, results: list[str], notes: str) -> str:
        parts = [self.header(prepared)]
        for q, note in zip(self.queries, results):
            parts.append(f"-- {q.what}\n-- {q.population}\n{q.sql.rstrip()}  {note}")
        for label, body in self.answers:
            lines = []
            for para in body.strip().split("\n\n"):
                lines += textwrap.wrap(" ".join(para.split()), WIDTH, initial_indent="   ",
                                       subsequent_indent="   ") + [""]
            parts.append(f"/* Model answer ({label})\n\n" + "\n".join(lines).rstrip().replace("*/", "* /") + "\n*/")
        parts.append(notes)
        return "\n\n".join(parts) + "\n"


def run(con: sqlite3.Connection, sql: str, statements) -> tuple[Result | None, str | None]:
    """Run a query's statements read-only (a view becomes a TEMP view); the last result and any view created."""
    import re
    result = view = None
    for stmt in statements(sql):
        stmt = re.sub(r"\bDROP\s+VIEW\s+IF\s+EXISTS\s+(\w+)", r"DROP VIEW IF EXISTS temp.\1", stmt, flags=re.I)
        m = re.search(r"\bCREATE\s+VIEW\s+(\w+)", stmt, flags=re.I)
        if m:
            view = m.group(1)
            stmt = re.sub(r"\bCREATE\s+VIEW\b", "CREATE TEMP VIEW", stmt, flags=re.I)
        cur = con.execute(stmt)
        if cur.description:
            result = Result([c[0] for c in cur.description], cur.fetchall())
    return result, view


def notes_block(sections: list[dict], checks: list[tuple[str, Check, object]], release: str) -> str:
    """The closing comment: each section's requirements and instructor note, then the checks."""
    out = ["/* Notes"]
    wrap = lambda text, indent: textwrap.wrap(text, WIDTH, initial_indent=indent, subsequent_indent=indent + "   ")
    for sec in sections:
        out += ["", *wrap(f"{sec['label']}: {sec['title']}", "   ")]
        for item in sec["items"]:
            out += wrap(item, "   ")
        if sec.get("meaning"):
            out += wrap(f"Instructor note: {sec['meaning']}", "   ")
    out += ["", *wrap(f"Checks (each agreed on dataset release {release} when this file was built):", "   ")]
    for section, c, got in checks:
        shown = f"{c.expected:,.2f}" if isinstance(c.expected, float) else str(c.expected)
        out += wrap(f"{section}: {c.label}: {shown}", "   ")
    text = "\n".join(out).replace("*/", "* /")
    return text + "\n*/"


@dataclass
class Build:
    """What a chapter module's functions receive: the scripts being written and read-only data helpers."""
    scripts: dict[str, Script] = field(default_factory=dict)
    current: str = ""                        # the exercise or requirement being applied

    def script(self, file: str, title: str, checks_line: str, **kw) -> Script:
        s = self.scripts.get(file) or self.scripts.setdefault(file, Script(file, title, checks_line, **kw))
        if self.current and self.current not in s.sections:
            s.sections.append(self.current)
        return s

    @property
    def data(self):
        """facts/db.Data: the fiscal window (F, P, C, N) and read-only query helpers, as the notes use them. The chapter
        modules import the notes' context functions the same way: `sys.path` holds `facts/`, then `from notes import
        ch10` (the folder `facts/` is not a package, and `scripts/facts.py` would shadow it)."""
        import sys
        from paths import REPO
        if str(REPO / "facts") not in sys.path:
            sys.path.insert(0, str(REPO / "facts"))
        from db import Data
        if not hasattr(self, "_data"):
            self._data = Data()
        return self._data
