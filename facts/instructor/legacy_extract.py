"""The extraction the instructor builders used before 2026-10-05, frozen, taking the .qmd text as an argument.

Copied verbatim from scripts/companion/xlbuild/solutions.py as it stood before Phase 8 (the copy of that file is
facts/instructor/_solutions_before_phase8.py.txt); check_equivalence.py runs it on the text of commit 4feb03f, which
still holds the comments, and compares it with the current functions, which read the public text and render the rest.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO / "scripts", REPO / "scripts" / "companion"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
from xlbuild.notes import plain  # noqa: E402


def exercise_info(text: str, chapter, n: int) -> dict:
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


def _items(body: str) -> list[str]:
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"^:::.*?^:::\s*$", "", body, flags=re.M | re.S)          # callouts (Watch out, In Practice)
    out = []
    for chunk in re.split(r"\n\s*\n|\n(?=\s*- )", body):
        chunk = re.sub(r"^\s*- ", "", chunk.strip())
        if chunk and not chunk.startswith("#"):
            out.append(plain(chunk))
    return out


def requirement_info(text: str, name: str, label: str) -> dict:
    kind, n = label.split()
    note = re.search(rf"<!--\s*Instructor notes, {kind} {n}\b[^:]*:\s*(.*?)-->", text, flags=re.S)
    if kind == "Requirement":
        m = re.search(rf"^\*\*Requirement {n}: (.+?)\*\*(.*?)(?=^<!-- notes:|^\*\*Requirement \d|^##+ |\Z)", text,
                      flags=re.M | re.S)
        if not m:
            raise KeyError(f"{label} not found in {name}")
        title, items = plain(m.group(1)).rstrip("."), _items(m.group(2))
    else:
        m = re.search(rf"^{n}\. \*\*(.+?)\*\*(.*)$", text, flags=re.M)
        if not m:
            raise KeyError(f"{label} not found in {name}")
        title, items = plain(m.group(1)), [plain(m.group(2)).lstrip(" :")]
    return dict(title=title, requirements=items, note=plain(note.group(1)) if note else "")
