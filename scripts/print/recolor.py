"""Recolor the book's figure PDFs for print: every RGB color becomes its CMYK value or gray level.

    python scripts/print/recolor.py [--mode cmyk|gray] [--force]

Each visuals/pdf/<name>.pdf (the vector PDF that scripts/export_drawio_svgs.py exports from Draw.io) is
written to outputs/print/figures/<mode>/<name>.pdf with each `r g b rg` / `RG` operator of its page and
form content streams replaced by the palette's `c m y k k` / `K` or `g` / `G` (scripts/print/palette.py).
A color outside the palette, any other color operator, an image, a shading or a pattern stops the run,
so a figure can never reach the printer in RGB. filters/pdf-figures.lua points the print profiles at
these copies. A copy is rewritten only when its source or the palette changed (a manifest keeps
the SHA-256 of each source).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.print import palette  # noqa: E402
from scripts.print.pdfops import COLOR_OPERATORS, operations  # noqa: E402

SOURCE = ROOT / 'visuals/pdf'
TARGET = ROOT / 'outputs/print/figures'
MODES = ('cmyk', 'gray')
# Bump when the recoloring changes, so cached copies are rewritten (a palette change does it by itself).
VERSION = 1


def cache_key() -> str:
    palette_text = json.dumps(palette.FIGURE_COLORS, sort_keys=True)
    return f'{VERSION}:{hashlib.sha256(palette_text.encode()).hexdigest()[:16]}'


def number(value: float) -> str:
    text = f'{value:.4f}'.rstrip('0').rstrip('.')
    return text if text not in ('', '-0') else '0'


def replacement(rgb: list[float], stroke: bool, mode: str, where: str) -> bytes:
    key = palette.rgb_key(tuple(rgb))
    if key not in palette.FIGURE_COLORS:
        raise ValueError(f'{where}: color {key} is not in the print palette (scripts/print/palette.py)')
    _, cmyk, gray = palette.FIGURE_COLORS[key]
    if mode == 'cmyk':
        operands = ' '.join(number(value / 100) for value in cmyk)
        return f'{operands} {"K" if stroke else "k"}'.encode()
    return f'{number(gray)} {"G" if stroke else "g"}'.encode()


def recolor_stream(data: bytes, mode: str, where: str) -> tuple[bytes, int]:
    """The stream with its RGB colors replaced, and the number of replacements."""
    out, last, count = [], 0, 0
    for op in operations(data):
        if op.operator == 'BI':
            raise ValueError(f'{where}: inline image (the print palette covers vector figures only)')
        if op.operator == 'sh':
            raise ValueError(f'{where}: shading (not supported by the print palette)')
        if op.operator not in COLOR_OPERATORS:
            continue
        values = op.numbers()
        if op.operator in ('rg', 'RG') and values is not None and len(values) == 3:
            out.append(data[last:op.start])
            out.append(replacement(values, op.operator == 'RG', mode, where))
            last = op.end
            count += 1
        elif op.operator in ('g', 'G') and values is not None and len(values) == 1:
            continue  # gray is already printable in both modes
        else:
            raise ValueError(f'{where}: unexpected color operator {op.operator!r} '
                             f'({b" ".join(op.operands).decode("latin-1")})')
    out.append(data[last:])
    return b''.join(out), count


def content_xrefs(doc) -> list[int]:
    """The page content streams and every form XObject of the document."""
    xrefs = {xref for page in doc for xref in page.get_contents()}
    for xref in range(1, doc.xref_length()):
        if not doc.xref_is_stream(xref):
            continue
        subtype = doc.xref_get_key(xref, 'Subtype')
        if subtype == ('name', '/Form'):
            xrefs.add(xref)
        elif subtype == ('name', '/Image'):
            raise ValueError(f'image object {xref} (the print palette covers vector figures only)')
    for xref in range(1, doc.xref_length()):
        text = doc.xref_object(xref, compressed=True)
        for key in ('/Shading', '/Pattern'):
            if key in text:
                raise ValueError(f'object {xref} has a {key[1:]} resource (not supported by the print palette)')
    return sorted(xrefs)


def recolor_file(source: Path, target: Path, mode: str) -> int:
    import pymupdf as fitz  # PyMuPDF
    doc = fitz.open(source)
    count = 0
    for xref in content_xrefs(doc):
        data = doc.xref_stream(xref)
        new, replaced = recolor_stream(data, mode, f'{source.name} object {xref}')
        if replaced:
            doc.update_stream(xref, new)
            count += replaced
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.save(target, garbage=3, deflate=True)
    return count


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recolor_all(modes=MODES, force: bool = False, source: Path = SOURCE, target: Path = TARGET) -> dict:
    """Recolor every figure for each mode; returns {mode: {'written': n, 'kept': n, 'removed': n}}."""
    figures = sorted(source.glob('*.pdf'))
    if not figures:
        raise ValueError(f'No figure PDFs in {source}: run scripts/export_drawio_svgs.py first')
    summary = {}
    for mode in modes:
        folder = target / mode
        folder.mkdir(parents=True, exist_ok=True)
        manifest_path = folder / 'manifest.json'
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            manifest = {}
        if manifest.get('version') != cache_key():
            manifest = {'version': cache_key(), 'files': {}}
        files = manifest['files']
        written = kept = 0
        for figure in figures:
            out = folder / figure.name
            sha = digest(figure)
            if not force and files.get(figure.name) == sha and out.is_file():
                kept += 1
                continue
            recolor_file(figure, out, mode)
            files[figure.name] = sha
            written += 1
        names = {figure.name for figure in figures}
        removed = 0
        for stale in folder.glob('*.pdf'):
            if stale.name not in names:
                stale.unlink()
                files.pop(stale.name, None)
                removed += 1
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        summary[mode] = {'written': written, 'kept': kept, 'removed': removed}
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--mode', choices=MODES, action='append', help='Default: both.')
    parser.add_argument('--force', action='store_true', help='Rewrite every copy, not only changed ones.')
    args = parser.parse_args()
    for mode, counts in recolor_all(tuple(args.mode or MODES), args.force).items():
        print(f'{mode}: {counts["written"]} written, {counts["kept"]} unchanged, {counts["removed"]} removed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
