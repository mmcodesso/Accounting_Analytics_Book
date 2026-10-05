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


def selected_manifest(manifest: dict, chapter_id: str | None = None) -> dict:
    """Select a review deck without changing publication eligibility or inventory."""
    if chapter_id is None:
        return manifest
    chapters = [item for item in active_chapters(manifest) if item['id'] == chapter_id]
    if not chapters:
        raise ValueError(f'Unknown pilot/approved chapter: {chapter_id}')
    result = copy.deepcopy(manifest)
    result['chapters'] = chapters
    for field in ('public_assets', 'public_fragments'):
        result[field] = [rel for rel in manifest.get(field, [])
                         if not rel.startswith('shared/generated/chapter-')
                         or rel.startswith(f'shared/generated/{chapter_id}/')]
    return result


def source_checks(root: Path, manifest: dict, chapter_id: str | None = None) -> list[str]:
    from scripts.slides.refresh import check_fresh
    from scripts.slides.refresh_foundations import check_fresh as check_foundations
    from scripts.slides.refresh_excel import check_fresh as check_excel
    from scripts.slides.refresh_sql import check_fresh as check_sql
    from scripts.slides.refresh_bi import check_fresh as check_bi
    from scripts.slides.refresh_storytelling import check_fresh as check_storytelling
    selected = selected_manifest(manifest, chapter_id)
    errors = (verify_sources(root, selected)
              + (check_fresh(root) if chapter_id in (None, 'chapter-01') else [])
              + check_storytelling(root, selected)
              + check_foundations(root, selected) + check_excel(root, selected)
              + check_sql(root, selected) + check_bi(root, selected))
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
    # Quarto discovers all registered inputs even when previewing one file.
    # Stage their public includes, while editorial/freshness checks stay scoped.
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
                    require_clean(source_checks(root, updated, chapter_id))
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


def build(root: Path, manifest: dict, quarto: str, *, slides_only=False, include_pilot=False,
          chapter_id: str | None = None) -> None:
    if chapter_id and not slides_only:
        raise ValueError('--chapter requires --slides-only; full-site assembly validates all chapters')
    selected = selected_manifest(manifest, chapter_id)
    require_clean(source_checks(root, manifest, chapter_id))
    actual = subprocess.check_output([quarto, '--version'], text=True).strip()
    pinned = str(manifest['toolchain']['quarto'])
    if actual != pinned:
        raise ValueError(f'Quarto {pinned} is required; found {actual}. Review/version changes explicitly.')
    # Project discovery resolves includes for every registered input. It needs
    # the full disposable public stage even for a selected document render.
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
    if active_chapters(selected):
        for fmt in ('revealjs', 'pptx'):
            if chapter_id:
                # Quarto may clean its output root. Render into an isolated tree
                # before replacing only the selected chapter's finished outputs.
                relative = f'_build/focused/{chapter_id}/{fmt}'
                stage = root / 'slides' / relative
                reset_owned(root, stage)
                run(root, [quarto, 'render', 'slides/' + selected['chapters'][0]['source'],
                           '--to', fmt, '--output-dir', relative], env)
            else:
                reset_owned(root, root / 'slides/_build' / fmt)
                run(root, [quarto, 'render', 'slides', '--to', fmt, '--output-dir', f'_build/{fmt}'], env)
        if chapter_id:
            focused = root / 'slides/_build/focused' / chapter_id
            require_clean(verify_outputs(root, selected, build_root=focused))
            for fmt in ('revealjs', 'pptx'):
                destination = root / 'slides/_build' / fmt
                reset_owned(root, destination / chapter_id)
                shutil.copytree(focused / fmt, destination, dirs_exist_ok=True)
        else:
            require_clean(verify_outputs(root, selected))
    if not slides_only:
        run(root, [quarto, 'render', '--to', 'html'], env)
        assemble(root, manifest, include_pilot=include_pilot)
        validation_manifest = copy.deepcopy(manifest)
        if include_pilot:
            for chapter in active_chapters(validation_manifest): chapter['status'] = 'approved'
        require_clean(verify_outputs(root, validation_manifest, site=root / '_book'))
    report = {'quarto': actual, 'mode': 'slides' if slides_only else 'book-and-slides',
              'includes_pilot': include_pilot or slides_only,
              'chapters': [item['id'] for item in active_chapters(selected)],
              'automated_artifact_checks': 'passed', 'browser_review': 'not-run', 'powerpoint_review': 'not-run'}
    report_path = root / ('outputs/build/' + chapter_id + '/build-report.json' if chapter_id
                          else 'outputs/build/build-report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Build complete. Automated checks passed; consult the separate visual-review report.', flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate public source closure without rendering or opening data')
    parser.add_argument('--slides-only', action='store_true')
    parser.add_argument('--chapter', metavar='CHAPTER', help='Focus checks or slide builds on one active chapter')
    parser.add_argument('--include-pilot', action='store_true', help='Include pilot in the local review site; never used by publication CI')
    parser.add_argument('--refresh-shared', action='store_true')
    parser.add_argument('--preview', metavar='CHAPTER')
    parser.add_argument('--init-reference', action='store_true')
    parser.add_argument('--export-public', action='store_true')
    parser.add_argument('--quarto', help='Explicit Quarto executable, or set QUARTO_BIN')
    args = parser.parse_args()
    try:
        if args.chapter and (args.export_public or args.init_reference
                             or not (args.check or args.slides_only or args.preview)):
            raise ValueError('--chapter is only supported with --check, --slides-only, or --preview; export and full assembly require all chapters')
        if args.chapter and args.preview and args.chapter != args.preview:
            raise ValueError('--chapter must match the --preview chapter')
        chapter_id = args.chapter or args.preview
        manifest = load_manifest(ROOT / 'slides/manifest.yml')
        selected_manifest(manifest, chapter_id)
        if args.init_reference:
            initialize_reference(ROOT, args.quarto or find_quarto())
            return 0
        if args.refresh_shared:
            if chapter_id:
                if chapter_id != 'chapter-01':
                    raise ValueError('Focused refresh is currently supported for chapter-01 only')
                from scripts.slides.refresh import refresh
                from scripts.slides.refresh_storytelling import refresh as refresh_storytelling
                refresh(ROOT)
                refresh_storytelling(ROOT)
            else:
                refresh_all(ROOT)
        errors = source_checks(ROOT, manifest, chapter_id)
        if args.check and chapter_id:
            report_path = ROOT / 'outputs/build' / chapter_id / 'source-check-report.json'
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps({'chapter': chapter_id,
                'status': 'failed' if errors else 'passed',
                'dataset_free': not args.refresh_shared, 'errors': errors}, indent=2) + '\n', encoding='utf-8')
        require_clean(errors)
        if args.check:
            detail = 'explicit refresh completed' if args.refresh_shared else 'no dataset opened'
            print(f'Public source closure, provenance, notes, and privacy checks passed ({detail}).')
        elif args.export_public:
            from scripts.slides.export_public import export_public
            print(export_public(ROOT, manifest, include_pilot=args.include_pilot))
        elif args.preview:
            preview(ROOT, manifest, args.quarto or find_quarto(), args.preview)
        else:
            build(ROOT, manifest, args.quarto or find_quarto(), slides_only=args.slides_only,
                  include_pilot=args.include_pilot, chapter_id=chapter_id)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


def refresh_all(root: Path) -> None:
    """Explicit authoring refresh; ordinary builds never open datasets."""
    from scripts.slides.refresh import refresh
    refresh(root)
    from scripts.slides.refresh_foundations import refresh as refresh_foundations
    refresh_foundations(root)
    # Rebuild the book views of the same public semantics/calculations.
    # The focused public builder imports only chapters with shared inputs.
    run(root, [sys.executable, 'scripts/slides/refresh_book_figures.py'])
    # Cropped teaching views must follow the canonical Draw.io export.
    run(root, [sys.executable, 'scripts/export_drawio_svgs.py'])
    from scripts.slides.refresh_storytelling import refresh as refresh_storytelling
    refresh_storytelling(root)
    from scripts.slides.refresh_excel import refresh as refresh_excel
    refresh_excel(root)
    from scripts.slides.refresh_sql import refresh as refresh_sql
    refresh_sql(root)
    from scripts.slides.refresh_bi import refresh as refresh_bi
    refresh_bi(root)

if __name__ == '__main__':
    raise SystemExit(main())
