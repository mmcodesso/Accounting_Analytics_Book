"""Run every ```sql block in the Part III chapters against the read-only database.

Usage: python scripts/verify/sql_check.py [chapter-number ...] [--show]

Markers (HTML comments, stripped from the rendered book) placed on the line
before a block:
    <!-- sql-check: skip -->    a syntax template, not run
    <!-- sql-check: error -->   a deliberate error example; it must fail
    <!-- sql-check: view -->    creates or drops a view; run on an in-memory copy of the
                                statement as a TEMP view
A block can also take its marker from scripts/verify/sql_check_markers.txt (file, first line of the
block, mode), so the chapter text stays free of comments. Every other block must run without
error. The report lists each block's file, line,
row count of its last statement, run time, and the first rows with --show.
"""

from __future__ import annotations

import re
import sqlite3
import sys
import textwrap
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import DB, REPO  # noqa: E402
SLOW = 5.0
SIDECAR = Path(__file__).with_name("sql_check_markers.txt")


def sidecar_markers() -> dict[tuple[str, str], str]:
    """(chapter file, first line of the block) -> marker, from sql_check_markers.txt."""
    found: dict[tuple[str, str], str] = {}
    if SIDECAR.is_file():
        for raw in SIDECAR.read_text(encoding="utf-8").splitlines():
            if raw.strip() and not raw.lstrip().startswith("#"):
                rest, mode = raw.rsplit(" | ", 1)
                file, first = rest.split(" | ", 1)
                found[(file.strip(), first.strip())] = mode.strip()
    return found


SIDE = sidecar_markers()


def blocks(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)```\s*\{?\.?sql\b", lines[i])
        if m:
            indent = len(m.group(1))
            marker = ""
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0:
                mm = re.search(r"<!--\s*sql-check:\s*(\w+)\s*-->", lines[j])
                if mm:
                    marker = mm.group(1)
            body = []
            k = i + 1
            while k < len(lines) and not re.match(r"^\s*```\s*$", lines[k]):
                body.append(lines[k][indent:] if lines[k][:indent].strip() == "" else lines[k])
                k += 1
            if not marker:
                first = next((b.strip() for b in body if b.strip()), "")
                marker = SIDE.get((path.relative_to(REPO).as_posix(), first), "")
            yield i + 1, marker, textwrap.dedent("\n".join(body))
            i = k + 1
        else:
            i += 1


def statements(sql: str):
    buf = ""
    for line in sql.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                yield buf.strip()
            buf = ""
    if buf.strip() and not all(l.strip().startswith("--") for l in buf.strip().splitlines()):
        yield buf.strip()


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show = "--show" in sys.argv
    chapters = [int(a) for a in args] or [9, 10, 11, 12]
    con = sqlite3.connect(f"{DB.as_uri()}?mode=ro", uri=True)
    failures = 0
    for ch in chapters:
        for folder in sorted(REPO.glob(f"chapters/{ch:02d}-*")):
            for path in sorted(folder.glob("*.qmd")):
                for line, marker, sql in blocks(path):
                    where = f"{path.relative_to(REPO)}:{line}"
                    if marker == "skip":
                        print(f"SKIP  {where}")
                        continue
                    try:
                        start = time.perf_counter()
                        rows = None
                        for stmt in statements(sql):
                            if marker == "view":
                                stmt = re.sub(r"\bCREATE\s+VIEW\b", "CREATE TEMP VIEW", stmt, flags=re.I)
                            cur = con.execute(stmt)
                            rows = cur.fetchall() if cur.description else rows
                            cols = [c[0] for c in cur.description] if cur.description else None
                        took = time.perf_counter() - start
                        if marker == "error":
                            print(f"FAIL  {where}: expected an error, but it ran")
                            failures += 1
                            continue
                        n = len(rows) if rows is not None else "-"
                        flag = "SLOW" if took > SLOW else "ok  "
                        print(f"{flag}  {where}: {n} rows, {took:.2f}s")
                        if show and rows:
                            print("      ", cols)
                            for r in rows[:6]:
                                print("      ", r)
                    except sqlite3.Error as exc:
                        if marker == "error":
                            print(f"ok    {where}: fails as intended ({exc})")
                        else:
                            print(f"ERROR {where}: {exc}")
                            failures += 1
    print(f"{failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
