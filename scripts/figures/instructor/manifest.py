"""The manifest of the instructor figures: what each image was built from, so a rebuild skips what is current.

`instructor-notes/figures/manifest.json` records, for every built figure, the digest of its Draw.io source (the
file under facts/instructor/figures/), the digest of the generator module that wrote it, and the size and SHA-256
of its PDF.  `build_instructor.py --verify` compares these with the files on disk, with no dataset and no Draw.io, so a clone
or CI can tell a stale figure from a current one; `build_instructor.py --check` regenerates every source in memory and
compares it with the saved file, which catches a change in the data.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSION = 1


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_text_file(path: Path) -> str:
    """SHA-256 of a text file with Windows and Unix line endings treated alike (git converts them)."""
    return digest_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


class Manifest:
    def __init__(self, path: Path):
        self.path = path
        self.settings: dict = {}
        self.figures: dict[str, dict] = {}
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("version") != VERSION:
                raise ValueError(f"{path}: unsupported manifest version")
            self.settings = data.get("settings", {})
            self.figures = data.get("figures", {})

    def entry(self, figure_id: str) -> dict | None:
        return self.figures.get(figure_id)

    def record(self, figure_id: str, unit: str, source: Path, generator: Path, pdf: Path) -> None:
        self.figures[figure_id] = {
            "unit": unit,
            "source": digest_text_file(source),
            "generator": digest_text_file(generator),
            "pdf_sha256": digest_file(pdf),
            "pdf_bytes": pdf.stat().st_size,
        }

    def forget(self, figure_id: str) -> None:
        self.figures.pop(figure_id, None)

    def save(self, settings: dict) -> None:
        self.settings = settings
        ordered = {k: self.figures[k] for k in sorted(self.figures)}
        text = json.dumps({"version": VERSION, "settings": settings, "figures": ordered}, indent=1) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text, encoding="utf-8", newline="\n")
