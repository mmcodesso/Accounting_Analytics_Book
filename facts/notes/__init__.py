"""Generated instructor notes.

A hidden note in a chapter (an HTML comment such as "<!-- Instructor notes, Exercise 11.1: ... -->")
is generated from the data when the line before it is a marker:

    <!-- notes: ch11.ex1 -->
    <!-- Instructor notes, Exercise 11.1: ... -->

The note's text is a Jinja template, templates/<chapter>/<name>.md, which holds the whole comment.
Its values come from a context function in <chapter>.py, registered with @note, which queries the
data through facts/db.Data and states the qualitative claims the text makes with claim(...). A claim
that fails on a new dataset means the template's wording must change, not just its numbers.

Edit a note in its template, never in the .qmd: scripts/facts.py sync rewrites the comment, and it
refuses to overwrite a comment that was changed by hand since the last sync (notes.lock.json).
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import jinja2

HERE = Path(__file__).resolve().parent
FACTS = HERE.parent
REPO = FACTS.parent
TEMPLATES = HERE / "templates"
LOCK = FACTS / "notes.lock.json"
MARKER = re.compile(r"<!-- notes: (?P<key>[\w.-]+) -->\r?\n(?P<comment><!--.*?-->)", re.S)
CHAPTERS = ["ch02", "case1", "ch04", "ch05", "ch06", "ch07", "ch08", "case2", "ch09", "ch10", "ch11", "ch12", "case3", "ch13", "ch14", "ch15", "ch16", "appendix_a", "case4", "ch17", "ch18", "ch19"]          # the modules with notes, in book order


@dataclass
class Note:
    key: str
    file: str
    template: str
    context: Callable


NOTES: dict[str, Note] = {}


def note(key: str, file: str, template: str | None = None):
    """Register a context function for the note `key` in `file` (relative to the repository)."""
    def register(fn):
        chapter, name = key.split(".", 1)
        NOTES[key] = Note(key, file, template or f"{chapter}/{name}.md", fn)
        return fn
    return register


# --- formatting --------------------------------------------------------------------------------

def _half_up(x: float, places: int):
    """x rounded as Excel shows it: to 15 significant digits, then half away from zero (2,006.895 is 2,006.90, where
    Python's formatting of the binary float 2,006.894999... gives 2,006.89)."""
    from decimal import ROUND_HALF_UP, Decimal
    return Decimal(repr(float(f"{x:.15g}"))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def money(x: float) -> str:
    return f"{_half_up(x, 2):,.2f}"


def num(x: float, places: int = 0) -> str:
    return f"{_half_up(x, places):,.{places}f}"


def pct(x: float, places: int = 1) -> str:
    return f"{_half_up(100 * x, places):.{places}f}%"


def spct(x: float, places: int = 1) -> str:
    return f"{_half_up(100 * x, places):+.{places}f}%"


def count(x: int) -> str:
    return f"{x:,}"


ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES), undefined=jinja2.StrictUndefined,
                         keep_trailing_newline=False, autoescape=False)
ENV.filters.update(money=money, num=num, pct=pct, spct=spct, count=count)


# --- rendering ---------------------------------------------------------------------------------

class Claims:
    def __init__(self):
        self.failed: list[str] = []

    def __call__(self, condition: bool, text: str) -> None:
        if not condition:
            self.failed.append(text)


def load() -> dict[str, Note]:
    for chapter in CHAPTERS:
        importlib.import_module(f"notes.{chapter}")
    return NOTES


def render(n: Note, d) -> tuple[str, dict[str, Any], list[str]]:
    """The note's comment text on this dataset, its values, and the claims that fail."""
    claims = Claims()
    try:
        values = n.context(d, claims)
        text = ENV.get_template(n.template).render(**values, d=d).rstrip("\n")
    except Exception as exc:  # a dataset that lacks what the note describes: report it like a failed claim
        return "", {}, claims.failed + [f"cannot render on this dataset ({type(exc).__name__}: {exc})"]
    return text, values, claims.failed


def plain(value: Any) -> Any:
    """Values as JSON can hold them (tuples become lists, numbers stay numbers)."""
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return [plain(v) for v in sorted(value, key=repr)]
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):   # numpy scalars
        value = value.item()
    if isinstance(value, float):
        return round(value, 6)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def regions(path: Path) -> dict[str, tuple[int, int, str]]:
    """The generated notes in a .qmd: key -> (start, end, current comment text)."""
    text = path.read_text(encoding="utf-8")
    found = {}
    for m in MARKER.finditer(text):
        if m.group("key") in found:
            raise ValueError(f"{path}: note {m.group('key')} appears twice")
        found[m.group("key")] = (m.start("comment"), m.end("comment"), m.group("comment"))
    return found


def digest(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]


def read_lock() -> dict[str, str]:
    return json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}


def write_lock(lock: dict[str, str]) -> None:
    LOCK.write_text(json.dumps(dict(sorted(lock.items())), indent=1) + "\n", encoding="utf-8")
