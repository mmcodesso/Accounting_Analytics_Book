"""Check that the quick reference appendix covers the functions the book teaches, and only those.

For each tool (a `## ` section of appendices/c-quick-reference/appendix.qmd), two tests:
  - coverage: every function the tool's chapters call in their code (fenced blocks of the tool's language and inline
    code) is named somewhere in the tool's section;
  - no extras: every name in the first column of the section's tables occurs in the tool's chapters.
A name the chapters use only as a wrong answer or as a measure name goes in IGNORE, with the reason.

    python scripts/verify/quick_reference_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APPENDIX = REPO / "appendices" / "a-quick-reference" / "appendix.qmd"
FENCE = re.compile(r"^```\{?\.?([\w-]*)\}?[^\n]*\n(.*?)^```", re.M | re.S)
INLINE = re.compile(r"`([^`\n]+)`")

UPPER_CALL = re.compile(r"(?<![\w.\[#'])([A-Z][A-Z0-9_]*(?:\.[A-Z0-9]+)*)\s*\(")
M_CALL = re.compile(r"(?<![\w.])(#date|[A-Z][a-z]+\.[A-Z][A-Za-z]+)\s*\(")
SQL_CALL = re.compile(r"(?<![\w.'])([A-Za-z_][A-Za-z0-9_]*)\s*\(")

UPPER_NAME = re.compile(r"\b[A-Z][A-Z0-9_]*(?:\.[A-Z0-9]+)*\b")
M_NAME = re.compile(r"#date|\b[A-Z][a-z]+\.[A-Z][A-Za-z]+\b")
SQL_NAME = re.compile(r"\b(?:[A-Z][A-Z0-9_]+|[a-z]+(?=\())")

TOOLS = {
    "Excel": dict(chapters=range(1, 9), fences={"", "excel"}, call=UPPER_CALL, name=UPPER_NAME, case=True),
    "Power Query": dict(chapters=[*range(4, 9), *range(13, 17)], fences={"", "m", "powerquery"}, call=M_CALL,
                        name=M_NAME, case=True),
    "SQL": dict(chapters=range(9, 13), fences={"sql"}, call=SQL_CALL, name=SQL_NAME, case=False),
    "DAX": dict(chapters=range(13, 17), fences={"", "dax"}, call=UPPER_CALL, name=UPPER_NAME, case=True,
                appendix="b-publishing-security"),
}
IGNORE = {
    "SQL": {"DATEDIFF"},     # SQL Server's function, a wrong option in a Chapter 11 multiple-choice question
    "DAX": {"TTM"},          # part of a measure name, "Hours per Standard Hour TTM"
}
PLACEHOLDERS = {"FALSE", "TRUE", "A1", "ROWS"}     # argument values in the first column, not functions


def tool_files(spec: dict) -> list[Path]:
    files = [f for d in sorted((REPO / "chapters").iterdir())
             if d.name[:2].isdigit() and int(d.name[:2]) in spec["chapters"] for f in sorted(d.glob("*.qmd"))]
    if spec.get("appendix"):
        files += sorted((REPO / "appendices" / spec["appendix"]).glob("*.qmd"))
    return files


def code_of(text: str, fences: set[str]) -> list[str]:
    chunks = [body for lang, body in FENCE.findall(text) if lang.lower() in fences]
    return chunks + INLINE.findall(FENCE.sub("", text))


def sections(text: str) -> dict[str, str]:
    parts = re.split(r"(?m)^## (.+)$", text)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def first_cells(section: str) -> list[str]:
    """The first cell of every body row of every table in the section."""
    cells, header = [], True
    for line in section.splitlines():
        if not line.startswith("|"):
            header = True
            continue
        if re.match(r"^\|\s*:?-", line):
            header = False
            continue
        if not header:
            cells.append(line.split("|")[1])
    return cells


def occurs(name: str, text: str, case: bool) -> bool:
    return re.search(r"(?<![\w.#])" + re.escape(name) + r"(?![\w])", text, 0 if case else re.I) is not None


def main() -> int:
    appendix = sections(APPENDIX.read_text(encoding="utf-8"))
    problems, checked = [], 0
    for tool, spec in TOOLS.items():
        section = appendix.get(tool)
        if section is None:
            problems.append(f"the appendix has no '## {tool}' section")
            continue
        texts = [f.read_text(encoding="utf-8") for f in tool_files(spec)]
        book = "\n".join(texts)
        called = {m for t in texts for chunk in code_of(t, spec["fences"]) for m in spec["call"].findall(chunk)}
        called = {c.upper() if not spec["case"] else c for c in called} - IGNORE.get(tool, set())
        for name in sorted(called):
            checked += 1
            if not occurs(name, section, spec["case"]):
                problems.append(f"{tool}: the chapters use {name}, which the quick reference does not list")
        for cell in first_cells(section):
            for code in INLINE.findall(cell):
                for name in spec["name"].findall(code):
                    if len(name) < 2 or name in PLACEHOLDERS:
                        continue
                    checked += 1
                    if not occurs(name, book, spec["case"]):
                        problems.append(f"{tool}: the quick reference lists {name}, which the chapters never use")
    for problem in sorted(set(problems)):
        print(problem)
    print(f"{checked} names checked, {len(set(problems))} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
