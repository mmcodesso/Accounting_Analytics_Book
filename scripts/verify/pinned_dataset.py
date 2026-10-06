"""The dataset release this edition is verified against, read from _variables.yml.

    python scripts/verify/pinned_dataset.py                 # prints url= and sha= lines (for $GITHUB_OUTPUT)
    python scripts/verify/pinned_dataset.py --verify FILE   # exits 1 unless FILE has the pinned SHA-256

Release assets are immutable: a new build gets a new tag, so a mismatch means a wrong or corrupted download.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def pinned() -> tuple[str, str]:
    """The download URL of CharlesRiver.sqlite and its pinned SHA-256."""
    variables = yaml.safe_load((REPO / "_variables.yml").read_text(encoding="utf-8"))
    dataset = variables["dataset"]
    return f"{dataset['download']}/CharlesRiver.sqlite", dataset["sha256"]["sqlite"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--verify", type=Path, help="check this file against the pinned SHA-256")
    args = parser.parse_args()
    url, expected = pinned()
    if args.verify is None:
        print(f"url={url}")
        print(f"sha={expected}")
        return 0
    if not args.verify.is_file():
        print(f"missing: {args.verify}")
        return 1
    actual = sha256(args.verify)
    if actual != expected:
        print(f"SHA-256 mismatch for {args.verify}\n  expected {expected}\n  actual   {actual}")
        return 1
    print(f"{args.verify}: SHA-256 matches the pinned release")
    return 0


if __name__ == "__main__":
    sys.exit(main())
