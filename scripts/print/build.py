#!/usr/bin/env python3
"""Build the print interiors of the book for IngramSpark: one color, one black and white.

    python scripts/print/build.py [--color] [--bw] [--draft] [--skip-render] [--gs-bin PATH]

Both interiors are US Letter (8.5 x 11 in) without bleed and open on the title page: the printer takes
the cover as a file of its own. For each one the build

1. exports the figures (scripts/export_drawio_svgs.py) and recolors them in CMYK or gray
   (scripts/print/recolor.py);
2. renders the book with its Quarto profile (_quarto-print-color.yml or _quarto-print-bw.yml) into
   outputs/print/render/<color|bw>/;
3. removes LuaTeX's transparency groups and checks the result (scripts/print/preflight.py, stage latex);
4. writes PDF/X-1a:2001 with Ghostscript (scripts/print/pdfx.py) and checks it again (stage final);
5. copies it to outputs/print/<book name>_Print_Color.pdf or _Print_BW.pdf, with a JSON report.

Each interior's copyright page must carry its ISBN (isbn.paperback-color and isbn.paperback-bw in
_quarto.yml). Until both are filled in, only --draft builds, and its files are named _DRAFT. The print
files are never assets of the revision's release (scripts/release.py), and the digital PDF, EPUB, DOCX
and site are not touched. Never run it alongside another render of the book: LaTeX writes its
intermediate files to the project root.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.build_all import QUARTO_VERSION  # noqa: E402
from scripts.print import pdfx  # noqa: E402
from scripts.print.preflight import preflight, summary  # noqa: E402
from scripts.print.recolor import recolor_all  # noqa: E402
from scripts.release import read_revision  # noqa: E402
from scripts.slides.prepare import find_quarto  # noqa: E402

# variant -> (Quarto profile, figure and preflight mode, ISBN key, file suffix)
VARIANTS = {
    'color': ('print-color', 'cmyk', 'paperback-color', 'Print_Color'),
    'bw': ('print-bw', 'gray', 'paperback-bw', 'Print_BW'),
}
OUTPUT = ROOT / 'outputs/print'


def run(args: list[str], env: dict | None = None) -> None:
    print('+ ' + ' '.join(str(part) for part in args), flush=True)
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def read_config() -> dict:
    return yaml.safe_load((ROOT / '_quarto.yml').read_text(encoding='utf-8')) or {}


def git_state() -> dict:
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        return {'commit': None, 'dirty': None}
    return {'commit': commit, 'dirty': dirty}


def build(variants: list[str], draft: bool = False, skip_render: bool = False, gs_bin: str | None = None) -> int:
    config = read_config()
    isbns = {key: str(value or '').strip() for key, value in (config.get('isbn') or {}).items()}
    missing = [VARIANTS[v][2] for v in variants if not isbns.get(VARIANTS[v][2])]
    if missing and not draft:
        raise SystemExit(f'Fill in isbn.{" and isbn.".join(missing)} in _quarto.yml before building the files '
                         'for the printer, or build a --draft.')
    quarto = find_quarto()
    actual = subprocess.check_output([quarto, '--version'], text=True).strip()
    if actual != QUARTO_VERSION:
        raise SystemExit(f'Quarto {QUARTO_VERSION} is required; found {actual}.')
    gs = pdfx.find_ghostscript(gs_bin)
    title = str((config.get('book') or {}).get('title') or 'Accounting Analytics')
    book_name = read_revision(ROOT).book_name

    env = dict(os.environ)
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    env.pop('AA_DRAWIO_EXPORTS_READY', None)
    run([sys.executable, 'scripts/export_drawio_svgs.py'], env)
    # The exports are current: the pre-render hook of each render must not export again after the recoloring.
    env['AA_DRAWIO_EXPORTS_READY'] = '1'
    for mode, counts in recolor_all(tuple(VARIANTS[v][1] for v in variants)).items():
        print(f'figures ({mode}): {counts["written"]} recolored, {counts["kept"]} unchanged', flush=True)

    failed = []
    for variant in variants:
        profile, mode, isbn_key, suffix = VARIANTS[variant]
        started = time.time()
        rendered = OUTPUT / 'render' / variant / 'Accounting-Analytics.pdf'
        if not skip_render:
            run([quarto, 'render', '--profile', profile, '--to', 'pdf'], env)
        if not rendered.is_file():
            raise SystemExit(f'Expected {rendered}; render it first (without --skip-render).')
        work = OUTPUT / 'work' / variant
        latex = work / 'latex.pdf'
        groups = pdfx.strip_transparency_groups(rendered, latex)
        print(f'{variant}: removed {groups} transparency groups', flush=True)
        gate = preflight(latex, mode, 'latex', draft)
        print(summary(gate), flush=True)
        if not gate['ok']:
            failed.append(f'{variant} (LaTeX output)')
            continue
        final = work / 'pdfx.pdf'
        pdfx.to_pdfx(latex, final, title, gs, work)
        report = preflight(final, mode, 'final', draft)
        print(summary(report), flush=True)
        name = f'{book_name}_{suffix}{"_DRAFT" if draft else ""}.pdf'
        destination = OUTPUT / name
        report.update({
            'variant': variant, 'profile': profile, 'isbn': isbns.get(isbn_key) or None, 'draft': draft,
            'pdfx': pdfx.PDFX_NAMES[pdfx.PDFX_VERSION], 'output': str(destination.relative_to(ROOT)),
            'quarto': actual, 'ghostscript': gs, 'seconds': round(time.time() - started), **git_state(),
        })
        (OUTPUT / f'{book_name}_{suffix}{"_DRAFT" if draft else ""}.json').write_text(
            json.dumps(report, indent=2) + '\n', encoding='utf-8')
        if not report['ok']:
            failed.append(f'{variant} (PDF/X file)')
            continue
        shutil.copy2(final, destination)
        print(f'{variant}: {destination.relative_to(ROOT)} ({report["pages"]} pages)', flush=True)
    if failed:
        print('Preflight failed: ' + ', '.join(failed), flush=True)
        return 1
    print('Print interiors built. Upload each to IngramSpark, read its error report, and order a proof.', flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--color', action='store_true', help='Build the color interior (default: both).')
    parser.add_argument('--bw', action='store_true', help='Build the black-and-white interior (default: both).')
    parser.add_argument('--draft', action='store_true', help='Allow blank ISBNs; the files are named _DRAFT.')
    parser.add_argument('--skip-render', action='store_true', help='Reuse the last render of each profile.')
    parser.add_argument('--gs-bin', help='Path to gswin64c.exe (or set GS_BIN).')
    args = parser.parse_args()
    variants = [v for v, chosen in (('color', args.color), ('bw', args.bw)) if chosen] or ['color', 'bw']
    return build(variants, args.draft, args.skip_render, args.gs_bin)


if __name__ == '__main__':
    raise SystemExit(main())
