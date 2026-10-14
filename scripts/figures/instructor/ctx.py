"""The values behind an instructor guide, for the figures that illustrate it.

A figure draws what its guide states, so it takes its numbers from the guide's own context: `values("ch01.ex2")`
returns the dict that guides.py hands the template of Exercise 1.2 (a guide context in
facts/instructor/guide_contexts/, or the context of a registered note in facts/notes/).  `data()` is the
facts.db.Data of the dataset (window F, P, C, N, read-only queries) for a figure that needs rows the guide's
context does not hold.  Both open the dataset once.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for _p in (REPO / "scripts", REPO / "facts", REPO / "facts" / "instructor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


@lru_cache(maxsize=1)
def data():
    from db import Data
    return Data()


@lru_cache(maxsize=None)
def values(key: str) -> dict:
    import guides
    import notes
    return guides.get_context(key, data(), notes.Claims())
