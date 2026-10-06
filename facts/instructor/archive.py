"""Archive of every hidden comment of the book's .qmd files at commit 4feb03f (the last tree that holds them).

    python facts/instructor/archive.py            # write facts/instructor/baseline-4feb03f.json and verify the count

The archive records, per file and in order, each HTML comment's text, its 1-based line number (of the line where
the comment starts), the first text line after it, and its kind (note marker, generated-note body, instructor note,
answer key, expected values, dax-check / sql-check marker, other).  Nothing in the book's text may be lost when the
comments are gone from the public tree: the instructor package is built from this file and the rendered templates.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMMIT = "4feb03f"
OUT = Path(__file__).resolve().with_name("baseline-4feb03f.json")
COMMENT = re.compile(r"<!--.*?-->", re.S)
EXCLUDE = ("slides/", "shared/", "drafts/")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True).stdout


def book_files() -> list[str]:
    names = git("ls-tree", "-r", "--name-only", COMMIT).decode("utf-8").splitlines()
    return sorted(n for n in names if n.endswith(".qmd") and not n.startswith(EXCLUDE))


def kind_of(text: str, previous: dict | None) -> str:
    if re.match(r"<!-- notes: [\w.-]+ -->$", text):
        return "note-marker"
    if previous and previous["kind"] == "note-marker":
        return "note-body"
    if text.startswith("<!-- Answer key"):
        return "answer-key"
    if re.match(r"<!--\s*(dax|sql)-check:", text):
        return "check-marker"
    if re.match(r"<!--\s*Instructor notes", text):
        return "instructor-note"
    if re.match(r"<!--\s*Expected", text, re.I):
        return "expected-values"
    return "other"


def read(path: str) -> str:
    return git("show", f"{COMMIT}:{path}").decode("utf-8")


def build() -> dict:
    files = {}
    for path in book_files():
        text = read(path)
        lines = text.split("\n")
        items: list[dict] = []
        for m in COMMENT.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            after = text[m.end():].lstrip("\r\n \t")
            first_after = after.split("\n", 1)[0].rstrip("\r") if after else ""
            body = m.group(0)
            items.append(dict(index=len(items) + 1, line=line, text=body,
                              first_line_after=first_after, kind=kind_of(body, items[-1] if items else None)))
        if items:
            files[path] = items
        del lines
    return files


def main() -> int:
    files = build()
    total = sum(len(v) for v in files.values())
    kinds: dict[str, int] = {}
    for items in files.values():
        for it in items:
            kinds[it["kind"]] = kinds.get(it["kind"], 0) + 1
    chars = sum(len(it["text"]) for v in files.values() for it in v)
    data = dict(commit=COMMIT, comments=total, characters=chars, kinds=kinds, files=files)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(files)} files with comments, {total} comments, {chars} characters")
    print(kinds)
    return 0 if total == 401 else 1


if __name__ == "__main__":
    sys.exit(main())
