"""Contexts for instructor guides that no generated note supplies.

A guide template (facts/instructor/guides/<unit>/<file>.md) names a context in its front matter, `note: ch01.ex2`.
The key is looked up here first, then among the registered notes of facts/notes.  A context here is a function
`(d, claim)` like a note's: `d` is a facts.db.Data (window F, P, C, N and read-only queries), `claim(condition, text)`
records a statement the guide's wording makes about the data, and the return value is the dict of values the template
may use.  Add a module per chapter (ch01.py, case1.py, ...) and register each function with @context.

    from guide_contexts import context

    @context("ch01.ex2")
    def ex2(d, claim):
        n = d.one("SELECT COUNT(*) FROM SalesOrder")
        claim(n > 0, "the order table has rows")
        return {"orders": n}

Only add a value here when the guide's steps need it; a value no step uses does not belong in a guide.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable

CONTEXTS: dict[str, Callable] = {}


def context(key: str):
    def register(fn):
        CONTEXTS[key] = fn
        return fn
    return register


def load() -> dict[str, Callable]:
    for mod in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{mod.name}")
    return CONTEXTS
