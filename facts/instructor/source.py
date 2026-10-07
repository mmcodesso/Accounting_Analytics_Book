"""Where an instructor note comes from, now that the public text no longer holds the hidden comments.

A note for a label of the book (Exercise 11.1, Requirement 3, Milestone 1, Tutorial 13.1, the answer key of a
chapter) is looked up in this order:

1. the comment in the public .qmd, when the text still has one (a tree that predates the removal: behavior unchanged;
   this step is the caller's, which holds the text);
2. the note rendered from its template through the registry in facts/notes (the key is found from the registry's own
   keys and `file` fields: the file and the name `ex1`, `r3`, `m1`, `t2`, `mcq`; nothing maps a label by hand);
3. the literal comment archived from commit 4feb03f (facts/instructor/baseline-4feb03f.json), for the few notes that
   never had a template (Exercise B.1, Requirement 1 of the Part I case, the Guided Tutorial B.2 notes, and eleven
   answer keys).

A label that none of the three can supply raises KeyError: nothing is guessed.  The rendered text is the whole
comment, "<!-- Instructor notes, Exercise 11.1: ... -->", so callers cut it out of the markers the way they cut it
out of the .qmd.
"""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for p in (REPO / "facts", REPO / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import notes  # noqa: E402  (facts/notes)
from db import Data  # noqa: E402  (facts/db.py)

import json  # noqa: E402

ARCHIVE = HERE / "baseline-4feb03f.json"

_data: Data | None = None
_index: dict[tuple[str, str], str] | None = None
_cache: dict[str, str] = {}
_archive: dict | None = None


def data() -> Data:
    """The dataset the notes render on (scripts/paths.py: datasets/, or CHARLESRIVER_DATA), opened once."""
    global _data
    if _data is None:
        _data = Data()
    return _data


def rel(path: Path | str) -> str:
    """A repository-relative path with forward slashes, as the registry's `file` field spells it."""
    p = Path(path)
    if not p.is_absolute():
        return p.as_posix()
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:                      # a file outside the repository has no registry entry and no archive
        return p.as_posix()


def index() -> dict[tuple[str, str], str]:
    """(file, name) -> key for every registered note, from the registry's keys and file fields."""
    global _index
    if _index is None:
        _index = {}
        for key, n in notes.load().items():
            name = key.split(".", 1)[1]
            if (n.file, name) in _index:
                raise ValueError(f"two notes named {name} in {n.file}")
            _index[(n.file, name)] = key
    return _index


def key_for(path: Path | str, name: str) -> str | None:
    return index().get((rel(path), name))


def rendered(key: str) -> str:
    """The note's whole comment text on the current dataset; a failed claim is a warning (the wording is stale)."""
    if key not in _cache:
        text, _values, failed = notes.render(notes.load()[key], data())
        if not text:
            raise RuntimeError(f"note {key} cannot be rendered: {failed}")
        for f in failed:
            warnings.warn(f"note {key}: claim fails on this dataset: {f}", stacklevel=3)
        _cache[key] = text
    return _cache[key]


def archive() -> dict:
    global _archive
    if _archive is None:
        _archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    return _archive


def archived_comment(path: Path | str, pattern: str) -> str | None:
    """The first literal (not generated) comment of the file in the archive that `pattern` matches."""
    items = archive()["files"].get(rel(path), [])
    for i, it in enumerate(items):
        if it["kind"] in ("note-marker", "note-body", "check-marker"):
            continue
        if re.search(pattern, it["text"], flags=re.S):
            return it["text"]
    return None


def note_comment(path: Path | str, name: str, pattern: str) -> str:
    """The comment for the label whose registry name is `name` (ex1, r3, m1, t2, mcq) in `path`, from the rendered
    template, else from the archive (the literal comment that `pattern` matches). The public text is the caller's
    first choice (it still holds the comments on a tree that predates their removal)."""
    key = key_for(path, name)
    if key is not None:
        return rendered(key)
    literal = archived_comment(path, pattern)
    if literal is not None:
        return literal
    raise KeyError(f"no instructor note for {name} of {rel(path)}: not in the text, not in the registry, "
                   "not in the archive")


def line_after(path: Path | str, name: str) -> str | None:
    """The first text line after the note `name` of `path` in the archive, that is, the first line after the end of
    the requirement it closed. A requirement's text ran from its heading to the note's marker; with the comments
    gone, this line marks the same end (None: no generated note of that name, or the note closed the file)."""
    key = key_for(path, name)
    if key is None:
        return None
    items = archive()["files"].get(rel(path), [])
    for i, it in enumerate(items):
        if it["text"] == f"<!-- notes: {key} -->":
            return items[i + 1]["first_line_after"] or None
    raise KeyError(f"note {key} is registered but not in the archive of {rel(path)}")
