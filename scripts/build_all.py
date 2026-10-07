#!/usr/bin/env python3
"""Build the book and its chapter slide decks; never deploy.

A deck is published as soon as slides/chapter-NN/index.qmd exists, like a chapter: there is no
approval step. --check runs the fast source checks (no Quarto, no dataset); --slides-only renders
the decks without the book; --preview CHAPTER serves one deck in the browser.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.slides import book_index
from scripts.slides.pptx_finish import finish as finish_pptx
from scripts.slides.prepare import deck_ids, find_quarto, prepare, reset_owned
from scripts.slides.verify import is_reveal_runtime_metadata, load_manifest, verify_outputs, verify_sources

ROOT = Path(__file__).resolve().parents[1]
QUARTO_VERSION = '1.9.36'
BOOK_URL = book_index.BOOK_URL


def require_clean(errors: list[str]) -> None:
    if errors:
        raise ValueError('\n'.join(errors))


def selected_decks(root: Path, chapter_id: str | None = None) -> list[str]:
    decks = deck_ids(root)
    if chapter_id is None:
        return decks
    if chapter_id not in decks:
        raise ValueError(f'No deck for {chapter_id}: expected slides/{chapter_id}/index.qmd')
    return [chapter_id]


def source_checks(root: Path, chapter_id: str | None = None) -> list[str]:
    errors, warnings = verify_sources(root, selected_decks(root, chapter_id), book_index.build(root))
    for warning in warnings:
        print(f'WARNING: {warning}', flush=True)
    return errors


def run(root: Path, args: list[str], env: dict | None = None) -> None:
    print('+ ' + ' '.join(str(part) for part in args), flush=True)
    subprocess.run(args, cwd=root, env=env, check=True)


def assemble(root: Path, decks: list[str]) -> None:
    """Copy only final artifacts, preserving complete Reveal relative paths."""
    site = root / '_book'
    if not (site / 'index.html').is_file(): raise ValueError('Book HTML must finish before assembly')
    target = site / 'slides'
    # This is an explicitly owned publication subtree, never a source directory.
    if target.resolve() != (root.resolve() / '_book/slides') or target.is_symlink():
        raise ValueError('Unsafe slide publication directory')
    if target.exists(): shutil.rmtree(target)
    if decks:
        reveal = root / 'slides/_build/revealjs'
        nested_build = next((path for path in reveal.rglob('_build') if path.is_dir()), None)
        if nested_build:
            raise ValueError(f'Nested build directory in Reveal resources: {nested_build}')
        shutil.copytree(reveal, target)
        for directory in target.glob('chapter-*'):
            if directory.name not in decks and directory.is_dir():
                shutil.rmtree(directory)
        for deck in decks:
            relative = Path(deck) / (deck + '.pptx')
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


def dependency_state(root: Path) -> tuple:
    """What a deck reads: the book sources, the exported figures, the slide theme, filters and shortcodes."""
    paths = [root / '_quarto.yml', root / '_variables.yml', root / 'slides/_quarto.yml']
    for folder, pattern in (('chapters', '*.qmd'), ('shared/fragments', '*.qmd'), ('visuals/svg', '*.svg'),
                            ('slides/theme', '*'), ('slides/filters', '*'), ('slides/shortcodes', '*')):
        paths += [p for p in (root / folder).rglob(pattern) if p.is_file()]
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths if p.exists())


def preview(root: Path, quarto: str, chapter_id: str) -> None:
    selected_decks(root, chapter_id)
    prepare(root, png=False)
    stop = threading.Event()
    failures: list[str] = []
    source = root / 'slides' / chapter_id / 'index.qmd'
    process = subprocess.Popen([quarto, 'preview', str(source.relative_to(root)), '--to', 'revealjs',
                                '--no-browser'], cwd=root)

    def watch():
        previous = dependency_state(root)
        while not stop.wait(1):
            try:
                current = dependency_state(root)
                if current != previous:
                    require_clean(source_checks(root, chapter_id))
                    prepare(root, png=False)
                    # Touch the deck to trigger Quarto's watcher once the new inputs are staged.
                    source.touch()
                    previous = dependency_state(root)
            except Exception as exc:
                failures.append(str(exc))
                process.terminate()
                return
    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    try:
        code = process.wait()
        if failures: raise RuntimeError(f'Preview refresh failed: {failures[0]}')
        if code: raise RuntimeError(f'Quarto preview exited with {code}')
    finally:
        stop.set()
        if process.poll() is None: process.terminate()
        thread.join(timeout=3)


def build(root: Path, quarto: str, *, slides_only=False, chapter_id: str | None = None) -> None:
    if chapter_id and not slides_only:
        raise ValueError('--chapter requires --slides-only; the full build renders every deck')
    decks = selected_decks(root, chapter_id)
    require_clean(source_checks(root, chapter_id))
    actual = subprocess.check_output([quarto, '--version'], text=True).strip()
    if actual != QUARTO_VERSION:
        raise ValueError(f'Quarto {QUARTO_VERSION} is required; found {actual}.')
    env = dict(os.environ)
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    # Export the book's figures first (cached by checksum): the decks stage these same files.
    # Set the hook bypass only after success, and only in this build's child environment.
    env.pop('AA_DRAWIO_EXPORTS_READY', None)
    run(root, [sys.executable, 'scripts/export_drawio_svgs.py'], env)
    env['AA_DRAWIO_EXPORTS_READY'] = '1'
    prepare(root, quarto=quarto)
    if not slides_only:
        downloads = root / 'outputs/build/downloads'
        reset_owned(root, downloads)
        for ext in ('pdf', 'epub', 'docx'):
            run(root, [quarto, 'render', '--to', ext], env)
            product = root / '_book' / f'Accounting-Analytics.{ext}'
            if not product.is_file(): raise ValueError(f'Expected book output was not created: {product}')
            shutil.copy2(product, downloads / f'book-latest.{ext}')
    if decks:
        for fmt in ('revealjs', 'pptx'):
            if chapter_id:
                # Quarto may clean its output root. Render into an isolated tree
                # before replacing only the selected chapter's finished outputs.
                relative = f'_build/focused/{chapter_id}/{fmt}'
                reset_owned(root, root / 'slides' / relative)
                run(root, [quarto, 'render', f'slides/{chapter_id}/index.qmd',
                           '--to', fmt, '--output-dir', relative], env)
            else:
                reset_owned(root, root / 'slides/_build' / fmt)
                run(root, [quarto, 'render', 'slides', '--to', fmt, '--output-dir', f'_build/{fmt}'], env)
        pptx_root = root / 'slides/_build' / (f'focused/{chapter_id}/pptx' if chapter_id else 'pptx')
        tokens = load_manifest(root / 'slides/theme/tokens.yml')
        for deck in decks:
            finish_pptx(pptx_root / deck / f'{deck}.pptx', tokens)
        if chapter_id:
            focused = root / 'slides/_build/focused' / chapter_id
            require_clean(verify_outputs(root, decks, build_root=focused, book_url=BOOK_URL))
            for fmt in ('revealjs', 'pptx'):
                destination = root / 'slides/_build' / fmt
                reset_owned(root, destination / chapter_id)
                shutil.copytree(focused / fmt, destination, dirs_exist_ok=True)
        else:
            require_clean(verify_outputs(root, decks, book_url=BOOK_URL))
    if not slides_only:
        run(root, [quarto, 'render', '--to', 'html'], env)
        assemble(root, decks)
        require_clean(verify_outputs(root, decks, site=root / '_book', book_url=BOOK_URL))
    report = {'quarto': actual, 'mode': 'slides' if slides_only else 'book-and-slides', 'chapters': decks,
              'automated_artifact_checks': 'passed'}
    report_path = root / ('outputs/build/' + chapter_id + '/build-report.json' if chapter_id
                          else 'outputs/build/build-report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Build complete. Automated checks passed; look at the slides before sharing them.', flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check the deck sources without rendering or opening data')
    parser.add_argument('--slides-only', action='store_true')
    parser.add_argument('--chapter', metavar='CHAPTER', help='Limit --check or --slides-only to one deck, e.g. chapter-01')
    parser.add_argument('--preview', metavar='CHAPTER')
    parser.add_argument('--quarto', help='Explicit Quarto executable, or set QUARTO_BIN')
    args = parser.parse_args()
    try:
        if args.chapter and not (args.check or args.slides_only or args.preview):
            raise ValueError('--chapter is only supported with --check, --slides-only, or --preview')
        if args.chapter and args.preview and args.chapter != args.preview:
            raise ValueError('--chapter must match the --preview chapter')
        chapter_id = args.chapter or args.preview
        if args.check:
            require_clean(source_checks(ROOT, chapter_id))
            print(f'Slide source checks passed for {len(selected_decks(ROOT, chapter_id))} deck(s) (no dataset opened).')
        elif args.preview:
            preview(ROOT, args.quarto or find_quarto(), args.preview)
        else:
            build(ROOT, args.quarto or find_quarto(), slides_only=args.slides_only, chapter_id=chapter_id)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
