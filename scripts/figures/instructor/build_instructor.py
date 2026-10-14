#!/usr/bin/env python3
"""Build the figures of the instructor guides.

Usage:
    python scripts/figures/instructor/build_instructor.py --unit 6            # one unit (6, 06, case2, appB, C2, AB)
    python scripts/figures/instructor/build_instructor.py --figure IF-06-1-A  # one figure (a prefix selects several)
    python scripts/figures/instructor/build_instructor.py                     # every unit
    python scripts/figures/instructor/build_instructor.py --force             # export again even when current
    python scripts/figures/instructor/build_instructor.py --list              # declared figures and their state
    python scripts/figures/instructor/build_instructor.py --verify            # files only: no dataset, no Draw.io
    python scripts/figures/instructor/build_instructor.py --check             # regenerate in memory (needs the dataset)

A guide declares each figure in the front matter of its template (facts/instructor/guides/<unit folder>/*.md:
id, kind, purpose, shows, data) and places it with {{ figure('IF-06-1-A') }}.  A generator for it lives in
scripts/figures/instructor/fig_<unit>.py as FIGURES = {"IF-06-1-A": function}; the function returns a
drawio.Diagram drawn from the dataset.  This script writes the Draw.io source to
facts/instructor/figures/<unit folder>/<id>.drawio and exports the figure as a vector PDF, the way the book exports its
figures (visuals/pdf: Draw.io's cropped PDF, text kept as text), to instructor-notes/figures/<unit folder>/<id>.pdf;
`guides.py render` then links that PDF in place of the placeholder and `guides.py pdf` places it in the PDF notes.
manifest.json records what each PDF was built from, so unchanged figures are skipped.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for _p in (REPO / "scripts" / "figures", HERE, REPO / "scripts", REPO / "facts" / "instructor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from manifest import Manifest, digest_file, digest_text_file  # noqa: E402

GUIDES = REPO / "facts" / "instructor" / "guides"
SRC = REPO / "facts" / "instructor" / "figures"
OUT = REPO / "instructor-notes" / "figures"
MANIFEST = OUT / "manifest.json"
ID = re.compile(r"^IF-([0-9]{2}|C[1-4]|A[A-Z])-(\d+)-([A-Z])$")


@dataclass
class Figure:
    id: str
    code: str           # 06, C1, AB
    folder: str         # the unit folder under guides/, instructor-notes/ and figures/
    template: str       # the guide template that declares it
    kind: str
    purpose: str
    shows: str
    data: str

    @property
    def source(self) -> Path:
        return SRC / self.folder / f"{self.id}.drawio"

    @property
    def pdf(self) -> Path:
        return OUT / self.folder / f"{self.id}.pdf"

    @property
    def module(self) -> Path:
        return HERE / f"fig_{self.code.lower()}.py"


def normalize_unit(unit: str) -> str:
    """06, 6, case2, C2, appB, AB -> the code used in figure ids (06, C2, AB)."""
    unit = unit.strip()
    if unit.isdigit():
        return f"{int(unit):02d}"
    m = re.fullmatch(r"case(\d)", unit, re.I)
    if m:
        return f"C{m.group(1)}"
    m = re.fullmatch(r"app([A-Za-z])", unit, re.I)
    if m:
        return f"A{m.group(1).upper()}"
    return unit.upper()


def folder_of(code: str, guides_dir: Path = GUIDES) -> str | None:
    for path in sorted(guides_dir.iterdir()):
        name = path.name
        if code.isdigit() and name.startswith(f"chapter-{code}-"):
            return name
        if code.startswith("C") and name == f"case-part-{code[1:]}":
            return name
        if code.startswith("A") and name.startswith(f"appendix-{code[1:].lower()}-"):
            return name
    return None


def declared(guides_dir: Path = GUIDES) -> dict[str, Figure]:
    """Every figure the templates declare, by id."""
    from guides import split_front
    found: dict[str, Figure] = {}
    for folder in sorted(p for p in guides_dir.iterdir() if p.is_dir()):
        for template in sorted(folder.glob("*.md")):
            meta, _ = split_front(template.read_text(encoding="utf-8"))
            for f in meta.get("figures") or []:
                m = ID.match(f.get("id", ""))
                if not m:
                    raise ValueError(f"{template}: bad figure id {f.get('id')!r}")
                if f["id"] in found:
                    raise ValueError(f"figure id {f['id']} is declared twice")
                found[f["id"]] = Figure(f["id"], m.group(1), folder.name, template.name, f.get("kind", ""),
                                        f.get("purpose", ""), f.get("shows", ""), f.get("data", ""))
    return found


def load_generators(code: str) -> tuple[dict, Path | None]:
    path = HERE / f"fig_{code.lower()}.py"
    if not path.is_file():
        return {}, None
    spec = importlib.util.spec_from_file_location(f"instructor_fig_{code.lower()}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.FIGURES), path


def export_pdf_file(source: Path, target: Path, drawio_bin: Path | None = None) -> None:
    """Draw.io's cropped vector PDF of a figure (the export the book uses for its own figures)."""
    import export_drawio_svgs as exporter
    binary = drawio_bin or exporter.find_drawio_executable(None)
    for attempt in (1, 2):
        try:
            exporter.export_pdf(binary, source, target, crop=True)
            return
        except exporter.ExportError:
            if attempt == 2:
                raise


def state(fig: Figure, manifest: Manifest) -> str:
    """planned (no PDF), current, or stale (the files and the manifest disagree)."""
    entry = manifest.entry(fig.id)
    if not fig.pdf.is_file() and entry is None:
        return "planned"
    if entry is None or not fig.pdf.is_file() or not fig.source.is_file():
        return "stale"
    if digest_text_file(fig.source) != entry["source"] or digest_file(fig.pdf) != entry["pdf_sha256"]:
        return "stale"
    return "current"


def select(figures: dict[str, Figure], units: list[str] | None, prefixes: list[str] | None) -> list[Figure]:
    chosen = list(figures.values())
    if units:
        codes = {normalize_unit(u) for u in units}
        chosen = [f for f in chosen if f.code in codes]
    if prefixes:
        chosen = [f for f in chosen if any(f.id.startswith(p) for p in prefixes)]
    return chosen


def cmd_list(chosen: list[Figure], manifest: Manifest) -> int:
    counts: dict[str, int] = {}
    for f in chosen:
        s = state(f, manifest)
        gens, _ = load_generators(f.code)
        counts[s] = counts.get(s, 0) + 1
        print(f"{f.id:12s} {f.kind:11s} {s:8s} {'generator' if f.id in gens else '-':9s} {f.folder}")
    print(counts)
    return 0


def cmd_verify(chosen: list[Figure], manifest: Manifest, complete: bool) -> int:
    problems = 0
    by_code: dict[str, tuple[dict, Path | None]] = {}
    for f in chosen:
        s = state(f, manifest)
        gens, module = by_code.setdefault(f.code, load_generators(f.code))
        entry = manifest.entry(f.id)
        if s == "stale":
            print(f"STALE   {f.id}: the source, the PDF and the manifest disagree (run build_instructor.py --figure {f.id})")
            problems += 1
        elif s == "planned" and complete:
            print(f"MISSING {f.id}: not built")
            problems += 1
        if s != "planned":
            if f.id not in gens:
                print(f"NOGEN   {f.id}: built, but fig_{f.code.lower()}.py has no generator for it")
                problems += 1
            elif module and entry and digest_text_file(module) != entry["generator"]:
                print(f"note    {f.id}: the generator module changed since the build (run build_instructor.py --check)")
    ids = {f.id for f in chosen}
    for code, (gens, module) in by_code.items():
        for fid in gens:
            if fid not in ids and fid.startswith(f"IF-{code}-"):
                print(f"ORPHAN  {fid}: a generator with no declaration in a template")
                problems += 1
    counts: dict[str, int] = {}
    for f in chosen:
        counts[state(f, manifest)] = counts.get(state(f, manifest), 0) + 1
    print(f"verify: {counts}, {problems} problem(s)")
    return 1 if problems else 0


def cmd_check(chosen: list[Figure], manifest: Manifest) -> int:
    """Regenerate each figure's source in memory and compare it with the saved file."""
    problems = 0
    for f in chosen:
        gens, _ = load_generators(f.code)
        if f.id not in gens:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"{f.id}.drawio"
            gens[f.id]().save(path)
            fresh = path.read_text(encoding="utf-8")
        if not f.source.is_file() or f.source.read_text(encoding="utf-8").replace("\r\n", "\n") != fresh:
            print(f"DRIFT   {f.id}: the generator now draws something else (data or code changed); rebuild it")
            problems += 1
    print(f"check: {len(chosen)} figure(s), {problems} drifted")
    return 1 if problems else 0


def cmd_build(chosen: list[Figure], manifest: Manifest, force: bool) -> int:
    built = skipped = failed = 0
    total = 0
    for f in chosen:
        gens, module = load_generators(f.code)
        if f.id not in gens:
            print(f"skip    {f.id}: no generator in fig_{f.code.lower()}.py yet")
            continue
        try:
            diagram = gens[f.id]()
            f.source.parent.mkdir(parents=True, exist_ok=True)
            diagram.save(f.source)
            if not force and state(f, manifest) == "current":
                skipped += 1
                total += f.pdf.stat().st_size
                continue
            f.pdf.parent.mkdir(parents=True, exist_ok=True)
            export_pdf_file(f.source, f.pdf)
            manifest.record(f.id, f.folder, f.source, module, f.pdf)
            manifest.save({"format": "pdf", "crop": True})
            built += 1
            total += f.pdf.stat().st_size
            print(f"built   {f.id} ({f.pdf.stat().st_size // 1024} KB)")
        except Exception as exc:                          # noqa: BLE001 - one bad figure must not stop the unit
            failed += 1
            print(f"FAILED  {f.id}: {type(exc).__name__}: {exc}")
    print(f"{built} built, {skipped} current, {failed} failed; {total // 1024} KB of PDF figures")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--unit", action="append")
    ap.add_argument("--figure", action="append")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--complete", action="store_true", help="with --verify: every declared figure must be built")
    args = ap.parse_args(argv)
    figures = declared()
    chosen = select(figures, args.unit, args.figure)
    if not chosen:
        print("no figure matched", file=sys.stderr)
        return 1
    manifest = Manifest(MANIFEST)
    if args.list:
        return cmd_list(chosen, manifest)
    if args.verify:
        return cmd_verify(chosen, manifest, args.complete)
    if args.check:
        return cmd_check(chosen, manifest)
    return cmd_build(chosen, manifest, args.force)


if __name__ == "__main__":
    sys.exit(main())
