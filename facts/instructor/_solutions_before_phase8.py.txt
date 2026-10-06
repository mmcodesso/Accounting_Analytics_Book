"""Exercise, case, and capstone solutions: shared state and the text their Solution Notes quote.

A solution workbook starts from a verified chapter-end checkpoint (the "fresh copy of the workbook made after the
chapter's tutorials" the exercises ask for), adds one worksheet per exercise (named as the exercise says, such as
"Ex 4.1"), and gets a Solution Notes worksheet whose sections are the exercises: their requirements, the checks of
their results, and the instructor notes the book holds for them (read from the .qmd, where facts/notes keeps them
in step with the data).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from paths import REPO
from xlbuild.notes import Check, plain

MONEY, COUNT, RATIO, PCT = "#,##0.00", "#,##0", "0.0000", "0.00%"


@dataclass
class ExerciseBuild:
    wb: object
    src: str                                    # the CharlesRiver.xlsx path the queries read while building
    xlsx: Path
    year: int                                   # the report year (fiscal 2026 in the 2026 edition)
    checks: list = field(default_factory=list)  # (exercise, Check)
    found: dict = field(default_factory=dict)

    def check(self, exercise: str, label: str, expected, actual: str, tolerance: float = 0.005, fmt: str = MONEY):
        self.checks.append((exercise, Check(label, expected, actual, tolerance, fmt)))


def exercises_file(chapter: int | str) -> Path:
    if isinstance(chapter, str):                      # an appendix, by its letter
        return next((REPO / "appendices").glob(f"{chapter.lower()}-*")) / "_exercises.qmd"
    return next((REPO / "chapters").glob(f"{chapter:02d}-*")) / "_exercises.qmd"


def exercise_info(chapter: int | str, n: int) -> dict:
    """An exercise's title, its requirements as plain text, and its instructor note (without the comment markers)."""
    text = exercises_file(chapter).read_text(encoding="utf-8")
    start = re.search(rf"^\*\*Exercise {chapter}\.{n}:? (.+?)\*\*", text, flags=re.M)
    if not start:
        raise KeyError(f"Exercise {chapter}.{n} not found")
    nxt = re.search(r"^\*\*Exercise (\d+|[A-Z])\.\d+", text[start.end():], flags=re.M)
    body = text[start.end(): start.end() + nxt.start()] if nxt else text[start.end():]
    note = re.search(r"<!--\s*Instructor notes,[^:]*:\s*(.*?)-->", body, flags=re.S)
    visible = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    reqs = [plain(m.group(0)) for m in re.finditer(r"^\(\d+\) .+?(?=\n\(\d+\) |\n\*\*Deliverable|\Z)", visible,
                                                    flags=re.M | re.S)]
    return dict(title=plain(start.group(1)), requirements=reqs, note=plain(note.group(1)) if note else "")


def exercise_sections(chapter: int | str, done: list[str]) -> list[dict]:
    out = []
    for e in done:
        info = exercise_info(chapter, int(e.split(".")[1]))
        out.append(dict(label=f"Exercise {e}", title=info["title"], items=info["requirements"], meaning=info["note"]))
    return out


# --- cases and capstones: requirements and milestones ---------------------------------------------------------------

def _items(body: str) -> list[str]:
    """A requirement's lead paragraph and bullets as plain items, without callouts, headings, or comments."""
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"^:::.*?^:::\s*$", "", body, flags=re.M | re.S)          # callouts (Watch out, In Practice)
    out = []
    for chunk in re.split(r"\n\s*\n|\n(?=\s*- )", body):
        chunk = re.sub(r"^\s*- ", "", chunk.strip())
        if chunk and not chunk.startswith("#"):
            out.append(plain(chunk))
    return out


def requirement_info(source: Path, label: str) -> dict:
    """A case's Requirement N or Milestone N: its title, its text as items, and its instructor note."""
    kind, n = label.split()
    text = source.read_text(encoding="utf-8")
    note = re.search(rf"<!--\s*Instructor notes, {kind} {n}\b[^:]*:\s*(.*?)-->", text, flags=re.S)
    if kind == "Requirement":
        m = re.search(rf"^\*\*Requirement {n}: (.+?)\*\*(.*?)(?=^<!-- notes:|^\*\*Requirement \d|^##+ |\Z)", text,
                      flags=re.M | re.S)
        if not m:
            raise KeyError(f"{label} not found in {source.name}")
        title, items = plain(m.group(1)).rstrip("."), _items(m.group(2))
    else:
        m = re.search(rf"^{n}\. \*\*(.+?)\*\*(.*)$", text, flags=re.M)
        if not m:
            raise KeyError(f"{label} not found in {source.name}")
        title, items = plain(m.group(1)), [plain(m.group(2)).lstrip(" :")]
    return dict(title=title, requirements=items, note=plain(note.group(1)) if note else "")


def requirement_sections(source: Path, done: list[str]) -> list[dict]:
    out = []
    for label in done:
        info = requirement_info(source, label)
        out.append(dict(label=label, title=info["title"], items=info["requirements"], meaning=info["note"]))
    return out
