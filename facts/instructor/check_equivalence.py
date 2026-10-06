"""Proof that the instructor builders no longer need the hidden comments of the public text.

    python facts/instructor/check_equivalence.py

For every exercise, requirement and milestone of the book (found in the text of commit 4feb03f, which still holds the
comments) it compares

  old: the frozen extraction (legacy_extract.py) run on the 4feb03f text of the file, and
  new: scripts/companion/xlbuild/solutions.py (exercise_info, requirement_info) run on the file as it is now,
       whose comments are gone, so every note comes from the rendered template or from the archive,

on the title, the requirements (items) and the note.  A label whose old note is empty must raise KeyError in the
new code (nothing is guessed).  Prints the differences and the totals; exit status 1 if there is any.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for p in (REPO / "scripts", REPO / "scripts" / "companion", REPO / "facts", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import archive as arch  # noqa: E402  (facts/instructor/archive.py)
import legacy_extract as legacy  # noqa: E402
from xlbuild import solutions  # noqa: E402


def labels() -> list[tuple[str, str, object]]:
    """(file, kind, argument) for every exercise, requirement and milestone found in the 4feb03f text."""
    out = []
    for path in arch.book_files():
        text = arch.read(path)
        name = Path(path).name
        if name == "_exercises.qmd":
            for ch, n in re.findall(r"^\*\*Exercise (\d+|[A-Z])\.(\d+)", text, flags=re.M):
                out.append((path, "exercise", (int(ch) if ch.isdigit() else ch, int(n))))
        if path.startswith("cases/") or re.match(r"chapters/1[789]-", path):
            for n in re.findall(r"^\*\*Requirement (\d+):", text, flags=re.M):
                out.append((path, "label", f"Requirement {n}"))
            for n in sorted(set(re.findall(r"<!--\s*Instructor notes, Milestone (\d+)\b", text))):
                out.append((path, "label", f"Milestone {n}"))
    return out


def dax_differences() -> tuple[int, list[str]]:
    """The Power BI builders' dax_blocks (pbibuild.reports, pbibuild.audit_monitoring) on today's files equal the
    marker reading of the 4feb03f text, for every file and kind."""
    import importlib
    import daxblocks
    reports = importlib.import_module("pbibuild.reports")
    monitoring = importlib.import_module("pbibuild.audit_monitoring")
    compared, differences = 0, []
    for path in arch.book_files():
        old = arch.read(path).replace(chr(13) + chr(10), chr(10))
        if "<!-- dax-check:" not in old:
            continue
        for kind in ("measure", "column", "table", "query", "skip"):
            want = daxblocks.blocks_with_markers(old, kind)
            got = reports.dax_blocks(REPO / path, kind)
            if path.startswith("chapters/16-"):                    # audit_monitoring reads its chapter's files by name
                got_m = monitoring.dax_blocks(Path(path).name, kind)
                if got_m != want:
                    differences.append(f"pbibuild.audit_monitoring {path} {kind}")
            compared += len(want)
            if got != want:
                differences.append(f"pbibuild.reports {path} {kind}: {len(want)} blocks then, {len(got)} now")
    return compared, differences


def main() -> int:
    differences, same, no_note, total = [], 0, 0, 0
    for path, kind, arg in labels():
        total += 1
        old_text = arch.read(path)
        try:
            if kind == "exercise":
                ch, n = arg
                old = legacy.exercise_info(old_text, ch, n)
                new_call = lambda: solutions.exercise_info(ch, n)
                tag = f"Exercise {ch}.{n}"
            else:
                old = legacy.requirement_info(old_text, path, arg)
                new_call = lambda: solutions.requirement_info(REPO / path, arg)
                tag = f"{path} {arg}"
        except KeyError as e:
            differences.append(f"{path} {arg}: the old code cannot read it ({e})")
            continue
        try:
            new = new_call()
        except KeyError as e:
            if old["note"] == "":
                no_note += 1               # no note before, none now: loud, not guessed
                continue
            differences.append(f"{tag}: the new code has no note ({e})")
            continue
        for field in ("title", "requirements", "note"):
            if old[field] != new[field]:
                differences.append(f"{tag}: {field} differs\n    old: {str(old[field])[:300]}\n    new: {str(new[field])[:300]}")
                break
        else:
            if old["note"] == "":
                differences.append(f"{tag}: the old note was empty but the new code supplies one")
            else:
                same += 1
    compared, dax = dax_differences()
    differences += [f"DAX blocks: {d}" for d in dax]
    for d in differences:
        print("DIFF", d)
    print(f"{compared} marked DAX blocks read by the Power BI builders' functions: {len(dax)} difference(s)")
    print(f"{total} labels: {same} identical (title, requirements and note), {no_note} with no note in either, "
          f"{len(differences)} difference(s)")
    return 1 if differences else 0


if __name__ == "__main__":
    sys.exit(main())
