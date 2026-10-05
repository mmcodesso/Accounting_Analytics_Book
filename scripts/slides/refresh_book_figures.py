#!/usr/bin/env python3
"""Refresh canonical Chapters 1–4 and 6–16 book figures used by shared slide inputs.

This focused public entry point imports only those chapters and their public
figure helpers. It never imports the full-book builder or a dataset generator.
Set CHARLESRIVER_DATA to the directory containing the pinned SQLite/XLSX files.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.slides.refresh import sha256
from scripts.slides.verify import load_manifest


def main() -> int:
    folder = Path(os.environ.get("CHARLESRIVER_DATA", ROOT / "datasets")).resolve()
    pins = load_manifest(ROOT / "_variables.yml")["dataset"]["sha256"]
    # Chapter 1's worksheet view reads workbook sheet names as well as SQLite rows.
    inputs = {suffix: folder / f"CharlesRiver.{suffix}" for suffix in ("sqlite", "xlsx")}
    before = {suffix: sha256(path) for suffix, path in inputs.items()}
    for suffix, value in before.items():
        if value != pins[suffix]:
            raise ValueError(f"CharlesRiver.{suffix} differs from _variables.yml; book figures were not changed.")
    sys.path.insert(0, str(ROOT / "scripts/figures"))
    import ch01
    import ch02
    import ch03
    import ch04
    import ch06
    import ch07
    import ch08
    import ch09
    import ch10
    import ch11
    import ch12
    import ch13
    import ch14
    import ch15
    import ch16

    destination = ROOT / "visuals/src"
    destination.mkdir(parents=True, exist_ok=True)
    for chapter in (ch01, ch02, ch03, ch04, ch06, ch07, ch08, ch09, ch10, ch11, ch12,
                    ch13, ch14, ch15, ch16):
        for name, build in chapter.FIGURES.items():
            path = destination / f"{name}.drawio"
            build().save(path)
            print(f"refreshed {path.relative_to(ROOT).as_posix()}")
    for suffix, path in inputs.items():
        if sha256(path) != before[suffix]:
            raise RuntimeError(f"CharlesRiver.{suffix} changed during the read-only figure refresh.")
    print("Chapters 1–4 and 6–16 book figures refreshed; pinned SQLite and workbook checksums unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
