#!/usr/bin/env python3
"""Rebuild the generated figure sources in visuals/src/ from code and the dataset.

Usage:
    python scripts/figures/build.py                    # every figure
    python scripts/figures/build.py --chapter 3        # one chapter
    python scripts/figures/build.py --figure fig-03-07 # figures whose name starts with this

The .drawio files stay the editable sources: the pre-render hook exports them
as usual. If you hand-edit a generated figure, port the edit here or remove the
figure from its chapter module, or the next build will overwrite it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ch01  # noqa: E402
import ch02  # noqa: E402
import ch03  # noqa: E402
import ch04  # noqa: E402
import ch05  # noqa: E402
import ch06  # noqa: E402
import ch07  # noqa: E402
import ch08  # noqa: E402
import ch09  # noqa: E402
import ch10  # noqa: E402
import ch11  # noqa: E402
import ch12  # noqa: E402
import ch13  # noqa: E402
import ch14  # noqa: E402
import ch15  # noqa: E402
import ch16  # noqa: E402
from data import REPO_ROOT  # noqa: E402

SRC_DIR = REPO_ROOT / "visuals" / "src"
CHAPTERS = {1: ch01.FIGURES, 2: ch02.FIGURES, 3: ch03.FIGURES, 4: ch04.FIGURES, 5: ch05.FIGURES,
            6: ch06.FIGURES, 7: ch07.FIGURES, 8: ch08.FIGURES, 9: ch09.FIGURES,
            10: ch10.FIGURES, 11: ch11.FIGURES, 12: ch12.FIGURES,
            13: ch13.FIGURES, 14: ch14.FIGURES, 15: ch15.FIGURES,
            16: ch16.FIGURES}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chapter", type=int, action="append", choices=sorted(CHAPTERS))
    parser.add_argument("--figure", action="append", help="Name prefix, such as fig-03-07.")
    args = parser.parse_args()

    selected = 0
    for chapter, figures in CHAPTERS.items():
        if args.chapter and chapter not in args.chapter:
            continue
        for name, build in figures.items():
            if args.figure and not any(name.startswith(prefix) for prefix in args.figure):
                continue
            diagram = build()
            path = SRC_DIR / f"{name}.drawio"
            diagram.save(path)
            print(f"wrote {path.relative_to(REPO_ROOT)}")
            selected += 1

    if not selected:
        print("No figures matched.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
