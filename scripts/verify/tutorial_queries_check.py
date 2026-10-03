"""Check that the tutorial SQL blocks of chapters 9-11 equal the queries of their dbbrowser.Script
(comment line plus query, in order), and that the final header block equals HEADER."""
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import FIGURES, REPO  # noqa: E402

sys.path.insert(0, str(FIGURES))
import ch09, ch10, ch11, ch12  # noqa: E402

CHAPTERS = {9: ("09-sql-essentials", ch09.CHAPTER09), 10: ("10-joining-and-summarizing", ch10.CHAPTER10),
            11: ("11-analytical-queries", ch11.CHAPTER11),
            12: ("12-sql-audit-analytics", ch12.CHAPTER12)}


def sql_blocks(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)```sql\s*$", lines[i])
        if m:
            body, k = [], i + 1
            while not re.match(r"^\s*```\s*$", lines[k]):
                body.append(lines[k])
                k += 1
            yield textwrap.dedent("\n".join(body)).strip("\n")
            i = k + 1
        else:
            i += 1


problems = 0
for n, (folder, script) in CHAPTERS.items():
    blocks = []
    for path in sorted((REPO / "chapters" / folder).glob("_tutorial-*.qmd")):
        blocks += list(sql_blocks(path))
    # A step may show an earlier version of a query under the same comment; the script holds
    # the last version.
    last = {}
    for b in blocks:
        if b.startswith("-- Tutorial"):
            last.pop(b.splitlines()[0], None)
            last[b.splitlines()[0]] = b
    tutorial = list(last.values())
    expected = [f"{c}\n{s}" for _, c, s in script.queries]
    if tutorial != expected:
        problems += 1
        print(f"chapter {n}: {len(tutorial)} tutorial blocks, {len(expected)} queries")
        for t, e in zip(tutorial, expected):
            if t != e:
                print("  TEXT:", t.splitlines()[0])
                for a, b in zip(t.splitlines(), e.splitlines()):
                    if a != b:
                        print("   text:", a, "\n   code:", b)
                        break
    headers = [b for b in blocks if b.startswith("/*")]
    if not headers or headers[-1] != script.header:
        problems += 1
        print(f"chapter {n}: the last header block differs from HEADER")
    print(f"chapter {n}: {len(tutorial)} queries checked")
print(problems, "problem(s)")
