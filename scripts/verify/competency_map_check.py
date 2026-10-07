"""Check the competency map appendix against the book's exercises and requirements.

Every item the four tables of appendices/d-competencies/appendix.qmd cite must exist (an exercise heading
`**Exercise C.N ...**` in a chapter's or an appendix's _exercises.qmd, or a `**Requirement N: ...**` of a comprehensive
case or capstone chapter), and every exercise and requirement of the book must appear at least once in each table.

    python scripts/verify/competency_map_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APPENDIX = REPO / "appendices" / "d-competencies" / "appendix.qmd"
ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV"}
EXERCISE = re.compile(r"^\*\*Exercise ([0-9A-Z]+\.\d+)", re.M)
REQUIREMENT = re.compile(r"^\*\*Requirement (\d+):", re.M)


def book_items() -> set[str]:
    items = set()
    for f in sorted(REPO.glob("chapters/*/_exercises.qmd")) + sorted(REPO.glob("appendices/*/_exercises.qmd")):
        items |= set(EXERCISE.findall(f.read_text(encoding="utf-8")))
    for f in sorted(REPO.glob("cases/part-*-case.qmd")):
        part = ROMAN[re.search(r"part-(\d)-case", f.name).group(1)]
        items |= {f"Part {part} R{n}" for n in REQUIREMENT.findall(f.read_text(encoding="utf-8"))}
    for f in sorted(REPO.glob("chapters/*/chapter.qmd")):
        found = REQUIREMENT.findall(f.read_text(encoding="utf-8"))
        if found:
            items |= {f"Ch. {int(f.parent.name[:2])} R{n}" for n in found}
    return items


def tables(text: str) -> dict[str, set[str]]:
    """Table ID -> the items its rows cite."""
    out, rows = {}, []
    for line in text.splitlines():
        if re.match(r"^\|\s*:?-", line):                          # the separator under a table's header
            continue
        if line.startswith("|"):
            rows.append(line)
            continue
        caption = re.match(r"^: .*\{#(tbl-d-\d+)\}", line)
        if caption:
            cited = set()
            for row in rows[1:]:                                   # the first row is the header
                cells = [c.strip() for c in row.strip("|").split("|")]
                cited |= set(re.findall(r"\b(?:\d+|[A-Z])\.\d+\b", cells[1]))
                for head, numbers in re.findall(r"((?:Part [IV]+|Ch\. \d+)) (R\d+(?:, R\d+)*)", cells[2]):
                    cited |= {f"{head} {n}" for n in re.findall(r"R\d+", numbers)}
            out[caption.group(1)] = cited
            rows = []
        elif line.strip():
            rows = []
    return out


def main() -> int:
    items = book_items()
    found = tables(APPENDIX.read_text(encoding="utf-8"))
    problems = []
    if len(found) != 4:
        problems.append(f"expected four tables, found {sorted(found)}")
    for tid, cited in sorted(found.items()):
        problems += [f"{tid}: cites {i}, which the book does not have" for i in sorted(cited - items)]
        problems += [f"{tid}: leaves out {i}" for i in sorted(items - cited)]
    for p in problems:
        print(p)
    print(f"{len(items)} items, {len(found)} tables, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
