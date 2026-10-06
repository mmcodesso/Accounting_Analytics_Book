"""Check that every {{< var key >}} shortcode in the book's text names a key of _variables.yml.

An unknown key does not fail a Quarto render: it prints "?var:key" in the page. This check fails instead, before
the render. The slides project has its own generated _variables.yml and is not checked here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SKIP = {"drafts", "_book", "outputs", ".quarto", "slides", "node_modules", ".git", "datasets"}
SHORTCODE = re.compile(r"\{\{<\s*var\s+([\w.\-]+)\s*>\}\}")


def resolves(variables: dict, key: str) -> bool:
    node = variables
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return not isinstance(node, dict)        # a key must name a value, not a section


def main() -> int:
    variables = yaml.safe_load((REPO / "_variables.yml").read_text(encoding="utf-8"))
    problems, uses = [], 0
    for path in sorted(REPO.rglob("*.qmd")):
        if SKIP & set(path.relative_to(REPO).parts):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for key in SHORTCODE.findall(line):
                uses += 1
                if not resolves(variables, key):
                    problems.append(f"{path.relative_to(REPO)}:{number}: unknown variable '{key}'")
    for problem in problems:
        print(problem)
    print(f"{uses} var shortcodes checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
