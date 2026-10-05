#!/usr/bin/env python3
"""Build the book and independently rendered chapter presentations; never deploy.

Default builds package approved decks only. --include-pilot creates a local review
site, while --slides-only renders pilot/approved decks without rebuilding the book.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.slides.prepare import find_quarto, initialize_reference, prepare, reset_owned
from scripts.slides.verify import (active_chapters, is_reveal_runtime_metadata, load_manifest,
                                  verify_outputs, verify_sources)

ROOT = Path(__file__).resolve().parents[1]


def require_clean(errors: list[str]) -> None:
    if errors:
        raise ValueError('\n'.join(errors))


def source_checks(root: Path, manifest: dict) -> list[str]:
    from scripts.slides.refresh import check_fresh
    from scripts.slides.refresh_foundations import check_fresh as check_foundations
    from scripts.slides.refresh_excel import check_fresh as check_excel
    from scripts.slides.refresh_sql import check_fresh as check_sql
    from scripts.slides.refresh_bi import check_fresh as check_bi
    errors = (verify_sources(root, manifest) + check_fresh(root)
              + check_foundations(root, manifest) + check_excel(root, manifest)
              + check_sql(root, manifest) + check_bi(root, manifest))
    config = load_manifest(root / 'slides/_quarto.yml')
    expected = [item['source'] for item in active_chapters(manifest)]
    if config.get('project', {}).get('render') != expected:
        errors.append('slides/_quarto.yml render list must match pilot/approved manifest sources exactly')
    for rel in ['slides/theme/reference-base.pptx', 'slides/filters/images.lua']:
        if not (root / rel).is_file(): errors.append(f'Missing build input: {rel}')
    return errors


def run(root: Path, args: list[str], env: dict | None = None) -> None:
    print('+ ' + ' '.join(str(part) for part in args), flush=True)
    subprocess.run(args, cwd=root, env=env, check=True)


def assemble(root: Path, manifest: dict, *, include_pilot: bool = False) -> None:
    """Copy only final artifacts, preserving complete Reveal relative paths."""
    site = root / '_book'
    if not (site / 'index.html').is_file(): raise ValueError('Book HTML must finish before assembly')
    target = site / 'slides'
    # This is an explicitly owned publication subtree, never a source directory.
    if target.resolve() != (root.resolve() / '_book/slides') or target.is_symlink():
        raise ValueError('Unsafe slide publication directory')
    if target.exists(): shutil.rmtree(target)
    selected = active_chapters(manifest, public_only=not include_pilot)
    if selected:
        reveal = root / 'slides/_build/revealjs'
        nested_build = next((path for path in reveal.rglob('_build') if path.is_dir()), None)
        if nested_build:
            raise ValueError(f'Nested build directory in Reveal resources: {nested_build}')
        shutil.copytree(reveal, target)
        selected_ids = {item['id'] for item in selected}
        for directory in target.glob('chapter-*'):
            if directory.name not in selected_ids and directory.is_dir():
                shutil.rmtree(directory)
        for chapter in selected:
            relative = Path(chapter['id']) / (chapter['id'] + '.pptx')
            shutil.copy2(root / 'slides/_build/pptx' / relative, target / relative)
        # Only generated runtime resources are allowed in the Reveal staging tree.
        forbidden = {'.qmd', '.py', '.lua', '.yml', '.yaml', '.drawio'}
        for path in target.rglob('*'):
            if (path.is_file() and path.suffix.lower() in forbidden
                    and not is_reveal_runtime_metadata(path, target)):
                raise ValueError(f'Unexpected source file in published slides: {path}')
    download_dir = site / 'downloads'
    download_dir.mkdir(exist_ok=True)
    for ext in ('pdf', 'epub', 'docx'):
        source = root / 'outputs/build/downloads' / f'book-latest.{ext}'
        if not source.is_file(): raise ValueError(f'Missing staged book download: {source}')
        shutil.copy2(source, download_dir / source.name)


def dependency_state(root: Path, manifest: dict) -> tuple:
    paths = [root / '_variables.yml', root / 'slides/manifest.yml', root / 'slides/_quarto.yml']
    paths += [p for p in (root / 'slides/theme').rglob('*') if p.is_file()]
    paths += [root / p for p in manifest.get('public_assets', []) + manifest.get('public_fragments', [])]
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)


def preview(root: Path, manifest: dict, quarto: str, chapter_id: str) -> None:
    chapter = next((item for item in active_chapters(manifest) if item['id'] == chapter_id), None)
    if chapter is None: raise ValueError(f'Unknown pilot/approved chapter: {chapter_id}')
    prepare(root, manifest)
    stop = threading.Event()
    failures: list[str] = []
    process = subprocess.Popen([quarto, 'preview', 'slides/' + chapter['source'], '--to', 'revealjs', '--no-browser'], cwd=root)
    def watch():
        watched_manifest = manifest
        previous = dependency_state(root, watched_manifest)
        while not stop.wait(1):
            try:
                current = dependency_state(root, watched_manifest)
                if current != previous:
                    updated = load_manifest(root / 'slides/manifest.yml')
                    require_clean(source_checks(root, updated))
                    prepare(root, updated)
                    # Touch just this authoring file to trigger Quarto's document watcher.
                    # Content is unchanged; newly staged dependencies precede the trigger.
                    (root / 'slides' / chapter['source']).touch()
                    watched_manifest = updated
                    previous = dependency_state(root, updated)
            except Exception as exc:
                failures.append(str(exc))
                process.terminate()
                return
    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    try:
        code = process.wait()
        if failures: raise RuntimeError(f'Preview shared-input refresh failed: {failures[0]}')
        if code: raise RuntimeError(f'Quarto preview exited with {code}')
    finally:
        stop.set()
        if process.poll() is None: process.terminate()
        thread.join(timeout=3)


def build(root: Path, manifest: dict, quarto: str, *, slides_only=False, include_pilot=False) -> None:
    require_clean(source_checks(root, manifest))
    actual = subprocess.check_output([quarto, '--version'], text=True).strip()
    pinned = str(manifest['toolchain']['quarto'])
    if actual != pinned:
        raise ValueError(f'Quarto {pinned} is required; found {actual}. Review/version changes explicitly.')
    prepare(root, manifest)
    env = dict(os.environ)
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    env['AA_SLIDES_INCLUDE_PILOT'] = '1' if include_pilot else '0'
    if not slides_only:
        # Export once for all four book formats. Set the hook bypass only after
        # success, and only in this build's child environment (never persist it).
        env.pop('AA_DRAWIO_EXPORTS_READY', None)
        run(root, [sys.executable, 'scripts/export_drawio_svgs.py'], env)
        env['AA_DRAWIO_EXPORTS_READY'] = '1'
        downloads = root / 'outputs/build/downloads'
        reset_owned(root, downloads)
        for ext in ('pdf', 'epub', 'docx'):
            run(root, [quarto, 'render', '--to', ext], env)
            product = root / '_book' / f'Accounting-Analytics.{ext}'
            if not product.is_file(): raise ValueError(f'Expected book output was not created: {product}')
            shutil.copy2(product, downloads / f'book-latest.{ext}')
    if active_chapters(manifest):
        for fmt in ('revealjs', 'pptx'):
            reset_owned(root, root / 'slides/_build' / fmt)
            run(root, [quarto, 'render', 'slides', '--to', fmt, '--output-dir', f'_build/{fmt}'], env)
        require_clean(verify_outputs(root, manifest))
    if not slides_only:
        run(root, [quarto, 'render', '--to', 'html'], env)
        assemble(root, manifest, include_pilot=include_pilot)
        validation_manifest = copy.deepcopy(manifest)
        if include_pilot:
            for chapter in active_chapters(validation_manifest): chapter['status'] = 'approved'
        require_clean(verify_outputs(root, validation_manifest, site=root / '_book'))
    report = {'quarto': actual, 'mode': 'slides' if slides_only else 'book-and-slides',
              'includes_pilot': include_pilot or slides_only,
              'chapters': [item['id'] for item in active_chapters(manifest)],
              'automated_artifact_checks': 'passed', 'browser_review': 'not-run', 'powerpoint_review': 'not-run'}
    report_path = root / 'outputs/build/build-report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Build complete. Automated checks passed; consult the separate visual-review report.', flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate public source closure without rendering or opening data')
    parser.add_argument('--slides-only', action='store_true')
    parser.add_argument('--include-pilot', action='store_true', help='Include pilot in the local review site; never used by publication CI')
    parser.add_argument('--refresh-shared', action='store_true')
    parser.add_argument('--preview', metavar='CHAPTER')
    parser.add_argument('--init-reference', action='store_true')
    parser.add_argument('--export-public', action='store_true')
    parser.add_argument('--quarto', help='Explicit Quarto executable, or set QUARTO_BIN')
    args = parser.parse_args()
    try:
        manifest = load_manifest(ROOT / 'slides/manifest.yml')
        if args.init_reference:
            initialize_reference(ROOT, args.quarto or find_quarto())
            return 0
        if args.refresh_shared:
            from scripts.slides.refresh import refresh
            refresh(ROOT)
            from scripts.slides.refresh_foundations import refresh as refresh_foundations
            refresh_foundations(ROOT)
            # Rebuild the book views of the same public semantics/calculations.
            # The focused public builder imports only chapters with shared inputs.
            run(ROOT, [sys.executable, 'scripts/slides/refresh_book_figures.py'])
            # Cropped teaching views must follow the canonical Draw.io export.
            run(ROOT, [sys.executable, 'scripts/export_drawio_svgs.py'])
            from scripts.slides.refresh_excel import refresh as refresh_excel
            refresh_excel(ROOT)
            from scripts.slides.refresh_sql import refresh as refresh_sql
            refresh_sql(ROOT)
            from scripts.slides.refresh_bi import refresh as refresh_bi
            refresh_bi(ROOT)
        require_clean(source_checks(ROOT, manifest))
        if args.check:
            print('Public source closure, provenance, notes, and privacy checks passed (no dataset opened).')
        elif args.export_public:
            from scripts.slides.export_public import export_public
            print(export_public(ROOT, manifest, include_pilot=args.include_pilot))
        elif args.preview:
            preview(ROOT, manifest, args.quarto or find_quarto(), args.preview)
        else:
            build(ROOT, manifest, args.quarto or find_quarto(), slides_only=args.slides_only, include_pilot=args.include_pilot)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
