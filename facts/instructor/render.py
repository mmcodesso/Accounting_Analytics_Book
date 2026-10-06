"""Render every generated instructor note from its template, and compare with the archived text.

    python facts/instructor/render.py [--db PATH]      # render 161 notes and check them against the archive

`render_all(d)` returns key -> comment text (the whole "<!-- ... -->" comment, as the old text held it) for each
note registered in facts/notes, on the data `d` (a facts.db.Data).  The engine is facts/notes/__init__.py
(`load()`, `render()`); nothing here knows a value.  `render_checked(d)` also returns the claims that fail.

The archive (baseline-4feb03f.json) holds each note's body as it stood at commit 4feb03f, after its marker
"<!-- notes: KEY -->"; `archived_notes()` returns key -> body.  `compare()` applies the comparison the old
`facts.py check` made: identical text after \r\n normalization (the engine's digest), else identical after
collapsing whitespace.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for p in (REPO / "facts", REPO / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import notes  # noqa: E402  (facts/notes)
from db import Data  # noqa: E402  (facts/db.py)
from paths import DB  # noqa: E402

ARCHIVE = HERE / "baseline-4feb03f.json"
MARKER_KEY = re.compile(r"<!-- notes: ([\w.-]+) -->$")


def render_checked(d: Data) -> dict[str, tuple[str, list[str]]]:
    """key -> (comment text, failed claims) for every registered note."""
    return {key: (text, failed) for key, (text, _values, failed) in
            ((k, notes.render(n, d)) for k, n in notes.load().items())}


def render_all(d: Data) -> dict[str, str]:
    """key -> the note's comment text on this data, for every registered note."""
    return {key: text for key, (text, _failed) in render_checked(d).items()}


def archive() -> dict:
    return json.loads(ARCHIVE.read_text(encoding="utf-8"))


def archived_notes() -> dict[str, dict]:
    """key -> dict(file, line, text) for each generated note in the archive (marker, then body)."""
    out: dict[str, dict] = {}
    for path, items in archive()["files"].items():
        for i, it in enumerate(items):
            m = MARKER_KEY.match(it["text"])
            if not m:
                continue
            body = items[i + 1]
            if body["kind"] != "note-body":
                raise ValueError(f"{path}:{it['line']}: the marker {m.group(1)} is not followed by a body")
            if m.group(1) in out:
                raise ValueError(f"note {m.group(1)} appears twice in the archive")
            out[m.group(1)] = dict(file=path, line=body["line"], text=body["text"])
    return out


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def compare(rendered: str, archived: str) -> str:
    """'identical', 'whitespace' (same words, other line breaks), or 'differs'."""
    if rendered.replace("\r\n", "\n") == archived.replace("\r\n", "\n"):
        return "identical"
    return "whitespace" if norm(rendered) == norm(archived) else "differs"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    args = ap.parse_args()
    d = Data(args.db)
    rendered = render_checked(d)
    arch = archived_notes()
    problems = 0
    counts: dict[str, int] = {}
    for key in sorted(set(rendered) | set(arch)):
        if key not in rendered or key not in arch:
            print(f"FAIL {key}: {'not registered' if key not in rendered else 'not in the archive'}")
            problems += 1
            continue
        text, failed = rendered[key]
        if notes.NOTES[key].file != arch[key]["file"]:
            print(f"FAIL {key}: registry file {notes.NOTES[key].file} but the archive has {arch[key]['file']}")
            problems += 1
        status = compare(text, arch[key]["text"])
        counts[status] = counts.get(status, 0) + 1
        if status == "differs" or failed:
            problems += 1
            print(f"FAIL {key}: {status}; failed claims: {failed}")
    print(f"{len(rendered)} notes rendered, {len(arch)} in the archive, {counts}, {problems} problem(s), "
          f"fiscal {d.F}-{d.C}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
