#!/usr/bin/env python3
"""The complete build in one command: every step from the checks to the published files, skipping what is current.

  python scripts/build_everything.py                  build everything that is out of date (nothing is committed or published)
  python scripts/build_everything.py --plan           show what would run and why, without running anything
  python scripts/build_everything.py --list           list the stages and the units inside them
  python scripts/build_everything.py --only guides    run one stage (or one unit, see --list); --skip, --from also work
  python scripts/build_everything.py --force all      run everything again (or --force STAGE, --force UNIT)
  python scripts/build_everything.py --no-office      leave out the Excel and Power BI Desktop builds
  python scripts/build_everything.py --print          also build the print interiors
  python scripts/build_everything.py --publish-dry-run    after the build, show what release.py publish would do
  python scripts/build_everything.py --publish        after the build, publish the revision (needs a clean, committed main)
  python scripts/build_everything.py --adopt          record the files that exist as built from the current sources

The stages, in order (each is skipped when it is current):

  gates               the fast checks, which fail early (keys, literals, citation file, deck sources, SQL, quick reference)
  figures             the generated figure sources, their SVG and PDF exports, the figure standard
  companion-sql       the SQL start files and solutions
  companion-excel     the Excel start files and solutions (drives Excel; one unit for each file)
  companion-pbi       the Power BI start files and solutions (drives Power BI Desktop)
  instructor-figures  the instructor guides' figures, drawn from the dataset and the built solution files
  guides              the instructor guides, rendered from their templates and checked
  instructor-pdf      the guides as PDF files, and Instructor-Notes.zip
  supplementary       the companion and solution files copied into supplementary/, where release.py takes them
  book                the PDF, EPUB and DOCX, both deck formats and the site (scripts/build_all.py)
  print               the print interiors (only with --print)
  checks              the generated notes and the unit tests
  publish             scripts/release.py publish (only with --publish or --publish-dry-run)

How "current" is decided. A unit records, after it succeeds, what it was built from: the git object of each input path
in the working tree (a file, or a folder, so one changed file changes it), the size and modification time of inputs
outside git (the dataset, the files another unit built), and any other value that matters. A Python builder's inputs are
the modules it imports, followed through the repository, so editing the Chapter 7 builder makes only Chapter 7's
solution out of date. A unit runs when an input differs from the record, when an output is missing, or when it was never
recorded. The record is outputs/build/everything.json (not tracked). A unit whose own inputs changed while it ran is not
recorded. The book and its decks use scripts/release.py's fingerprints, so publish agrees with this script.

A failed step stops the run and names the log; fix it and run the command again: the finished units are skipped.
The first run on a computer whose files are already built would rebuild all of them; --adopt records them instead
(it refuses a unit whose output is older than one of its inputs, unless you add --trust).
"""
from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import release  # noqa: E402  (working_tree, fingerprint, inputs_of, load_fingerprints, deck_ids)

PY = sys.executable
STORE = ROOT / 'outputs/build/everything.json'
LOG = ROOT / 'outputs/build/everything-last-run.log'
MANIFEST = ROOT / 'scripts/companion/manifest.yml'
COMPANION = 'outputs/companion'
DATASETS = ('datasets/CharlesRiver.sqlite', 'datasets/CharlesRiver.xlsx', 'datasets/CharlesRiver_support.xlsx')
OPT_IN = ('print', 'publish')
STAGE_ORDER = ('gates', 'figures', 'companion-sql', 'companion-excel', 'companion-pbi', 'instructor-figures', 'guides',
               'instructor-pdf', 'supplementary', 'book', 'print', 'checks', 'publish')
STAGE_TITLES = {
    'gates': 'The fast checks', 'figures': 'The book figures', 'companion-sql': 'SQL start files and solutions',
    'companion-excel': 'Excel start files and solutions', 'companion-pbi': 'Power BI start files and solutions',
    'instructor-figures': 'The instructor guides\' figures', 'guides': 'The instructor guides',
    'instructor-pdf': 'The instructor PDF files and package', 'supplementary': 'Files for the release (supplementary/)',
    'book': 'The book (PDF, EPUB, DOCX, decks, site)', 'print': 'The print interiors', 'checks': 'The notes and the unit tests',
    'publish': 'Publishing the revision'}
# What a rebuilt unit makes out of date downstream (used by --plan, which cannot see the files a run would change)
DOWNSTREAM = {'companion': ('instructor-figures', 'guides', 'instructor-pdf', 'instructor-package', 'supplementary'),
              'instructor-figures': ('guides', 'instructor-pdf', 'instructor-package'),
              'guides': ('instructor-pdf', 'instructor-package'), 'instructor-pdf': ('instructor-package',),
              'figures-sources': ('book',)}


# --- What a unit was built from ----------------------------------------------------------------------------------------

@dataclass
class Inputs:
    paths: list[str] = field(default_factory=list)      # repository paths (files or folders): the git object in the working tree
    sigs: list[str] = field(default_factory=list)       # paths outside git (ignored files, other units' outputs): size and time
    tokens: dict[str, str] = field(default_factory=dict)  # any other value that changes what is built

    def merged(self, other: 'Inputs') -> 'Inputs':
        return Inputs(self.paths + other.paths, self.sigs + other.sigs, {**self.tokens, **other.tokens})


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def signature(path: Path) -> str:
    """The size and modification time of a file, or one digest of those of every file in a folder."""
    if not path.exists():
        return 'missing'
    if path.is_file():
        stat = path.stat()
        return f'{stat.st_size}:{stat.st_mtime_ns}'
    digest = hashlib.sha1()
    for item in sorted(path.rglob('*')):
        if item.is_file() and '__pycache__' not in item.parts:
            stat = item.stat()
            digest.update(f'{item.relative_to(path).as_posix()}:{stat.st_size}:{stat.st_mtime_ns}\n'.encode())
    return digest.hexdigest()


def snapshot(inputs: Inputs, tree: str) -> dict[str, str]:
    snap: dict[str, str] = {}
    paths = sorted(set(inputs.paths))
    if paths:
        for path, obj in release.fingerprint(ROOT, tree, paths).items():
            snap[f'git:{path}'] = obj
    for path in sorted(set(inputs.sigs)):
        snap[f'sig:{path}'] = signature(ROOT / path)
    for key, value in sorted(inputs.tokens.items()):
        snap[f'token:{key}'] = str(value)
    return snap


def changes(old: dict[str, str], new: dict[str, str]) -> list[str]:
    return sorted(key.split(':', 1)[1] for key in set(old) | set(new) if old.get(key) != new.get(key))


def input_files(inputs: Inputs) -> list[Path]:
    """Every file behind the inputs, for --adopt's check that no input is newer than the output."""
    files: list[Path] = []
    for name in [*inputs.paths, *inputs.sigs]:
        path = ROOT / name
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return files


# --- The Python modules a builder imports -----------------------------------------------------------------------------

MODULE_ROOTS = [ROOT, ROOT / 'scripts', ROOT / 'scripts/companion', ROOT / 'scripts/figures', ROOT / 'facts',
                ROOT / 'facts/instructor']


def resolve_module(name: str) -> Path | None:
    parts = name.split('.')
    for base in MODULE_ROOTS:
        stem = base.joinpath(*parts)
        if stem.with_suffix('.py').is_file():
            return stem.with_suffix('.py')
        if (stem / '__init__.py').is_file():
            return stem / '__init__.py'
    return None


@functools.lru_cache(maxsize=None)
def local_imports(path: Path) -> tuple[Path, ...]:
    """The repository files a Python file imports (anywhere in it, also inside functions)."""
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except (OSError, SyntaxError):
        return ()
    found: set[Path] = set()
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names = [node.module, *(f'{node.module}.{alias.name}' for alias in node.names)]
        elif isinstance(node, ast.ImportFrom) and node.level:
            base = path.parent
            for _ in range(node.level - 1):
                base = base.parent
            stem = base.joinpath(*(node.module or '').split('.')) if node.module else base
            for candidate in ([stem.with_suffix('.py')] + [stem / f'{alias.name}.py' for alias in node.aliases]):
                if candidate.is_file():
                    found.add(candidate)
        for name in names:
            target = resolve_module(name)
            if target is not None:
                found.add(target)
    return tuple(sorted(found))


@functools.lru_cache(maxsize=None)
def closure(seeds: tuple[str, ...]) -> tuple[str, ...]:
    """The seeds and every repository module they import, followed through; the note templates of a notes module come too."""
    todo = [ROOT / seed for seed in seeds]
    seen: set[Path] = set()
    while todo:
        path = todo.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        todo.extend(local_imports(path))
    result = {rel(path) for path in seen}
    for path in seen:                                    # facts/notes/ch10.py reads facts/notes/templates/ch10
        if path.parent == ROOT / 'facts/notes' and (ROOT / 'facts/notes/templates' / path.stem).is_dir():
            result.add(f'facts/notes/templates/{path.stem}')
    return tuple(sorted(result))


def module_path(name: str) -> str:
    target = resolve_module(name)
    if target is None:
        raise ValueError(f'No module {name} in the repository')
    return rel(target)


def chapter_dir(chapter: object) -> str | None:
    """The folder of a chapter, or of an appendix named by its letter."""
    if str(chapter).isdigit():
        base, prefix = ROOT / 'chapters', f'{int(chapter):02d}-'
    else:
        base, prefix = ROOT / 'appendices', f'{str(chapter).lower()}-'
    hits = sorted(p for p in base.glob(prefix + '*') if p.is_dir())
    return rel(hits[0]) if hits else None


# --- Units and stages -------------------------------------------------------------------------------------------------

@dataclass
class Plan:
    commands: list[list[str]]
    reason: str                              # why it runs, or 'current'
    snapshot: dict[str, str] | None = None   # what is recorded when it succeeds
    recompute: Callable[['Context'], dict[str, str]] | None = None   # the snapshot after the run, to see that nothing moved


@dataclass
class Unit:
    key: str
    stage: str
    title: str
    commands: list[list[str]] = field(default_factory=list)
    inputs: Inputs | None = None
    outputs: tuple[str, ...] = ()            # paths (or globs) that must exist
    office: str | None = None                # 'excel' or 'pbi': needs that program
    always: bool = False                     # cheap or incremental by itself: runs every time
    custom: Callable[['Context', bool], Plan] | None = None
    dirties: tuple[str, ...] = ()            # what a rebuild of this unit makes out of date downstream (--plan)
    retries: int = 0                         # runs again once if its output matches RETRY_ON (an intermittent Windows error)

    @property
    def name(self) -> str:
        return f'{self.stage}/{self.key}'


RETRY_ON = 'Errno 22'


@dataclass
class Stage:
    name: str
    units: list[Unit]


class Context:
    def __init__(self, store: dict) -> None:
        self.store = store
        self._tree: str | None = None

    def tree(self, fresh: bool = False) -> str:
        if self._tree is None or fresh:
            tree = release.source_tree(ROOT)
            if tree is None:
                raise RuntimeError('This script needs a git checkout: the inputs are fingerprinted with git.')
            self._tree = tree
        return self._tree


def output_exists(pattern: str) -> bool:
    if any(ch in pattern for ch in '*?['):
        return any(ROOT.glob(pattern))
    return (ROOT / pattern).exists()


def missing_outputs(unit: Unit) -> list[str]:
    return [pattern for pattern in unit.outputs if not output_exists(pattern)]


def plan_unit(unit: Unit, ctx: Context, forced: bool) -> Plan:
    if unit.custom:
        return unit.custom(ctx, forced)
    if unit.always:
        return Plan(unit.commands, 'runs every time')
    snap = snapshot(unit.inputs, ctx.tree())
    again = lambda c: snapshot(unit.inputs, c.tree(fresh=True))          # noqa: E731
    record = ctx.store['units'].get(unit.name)
    if forced:
        reason = 'forced'
    elif record is None:
        reason = 'not recorded as built'
    elif (gone := missing_outputs(unit)):
        reason = f'missing {gone[0]}'
    elif (diff := changes(record['snapshot'], snap)):
        reason = 'changed: ' + ', '.join(diff[:3]) + (f' and {len(diff) - 3} more' if len(diff) > 3 else '')
    else:
        return Plan([], 'current', snap, again)
    return Plan(unit.commands, reason, snap, again)


# --- The companion files ----------------------------------------------------------------------------------------------

def folder_name(chapter: object) -> str:
    return f'Chapter{int(chapter):02d}' if str(chapter).isdigit() else f'Appendix{str(chapter).upper()}'


def solution_folder(entry: dict) -> str:
    if entry.get('folder'):
        return entry['folder']
    suffix = {'excel': 'exercises', 'pbi': 'exercises-pbi', 'sql': 'exercises-sql'}[entry['tool']]
    return f'{folder_name(entry["chapter"])}-{suffix}'


def chain_chapters(chain: dict) -> list:
    return list(chain.get('chapters') or [chain['chapter']])


def chain_outputs(chain: dict, manifest: dict) -> tuple[str, ...]:
    start = f'{COMPANION}/{manifest["start_folder"]}'
    outputs = [f'{start}/{folder_name(ch)}-companion.zip' for ch in chain_chapters(chain)]
    if chain['tool'] == 'sql' and chain.get('chapter') == 11:
        outputs.append(f'{start}/Setup_Part3_Views.sql')
    return tuple(outputs)


def solution_output(entry: dict, manifest: dict) -> str:
    return f'{COMPANION}/{manifest["solutions_folder"]}/{solution_folder(entry)}.zip'


def companion_base_inputs() -> Inputs:
    return Inputs(paths=['_variables.yml'], sigs=list(DATASETS))


def builder_seeds(entry: dict) -> list[str]:
    seeds = ['scripts/companion/build.py']
    if entry.get('builder'):
        seeds.append(module_path(entry['builder']))
    if entry.get('script'):                                  # an SQL chain: scripts/figures/ch09.py
        seeds.append(module_path(entry['script'].split('.')[0]))
    if entry.get('from'):
        seeds.append(module_path(entry['from'].split('.')[0]))
    return seeds


def entry_inputs(entry: dict, manifest: dict, chains: dict[str, dict]) -> Inputs:
    seeds = builder_seeds(entry)
    sigs: list[str] = []
    base = entry.get('base')
    if base:                                                 # the chain's checkpoint is the solution's start
        chain = chains[base['chain']]
        seeds.append(module_path(chain['builder']))
        sigs.extend(chain_outputs(chain, manifest))
    own = f'{COMPANION}/{manifest["solutions_folder"]}/{entry.get("folder", "")}/'
    for source in (entry.get('also_sources') or {}).values():
        if not str(source).startswith(own):                  # a file another unit built, not the unit's own output
            sigs.append(source)
    inputs = Inputs(paths=list(closure(tuple(seeds))), sigs=sigs,
                    tokens={'entry': json.dumps(entry, sort_keys=True, default=str),
                            'folders': f'{manifest["start_folder"]}/{manifest["solutions_folder"]}'})
    chapter_paths: list[str] = []
    for chapter in [*(entry.get('chapters') or []), *([entry['chapter']] if entry.get('chapter') is not None else [])]:
        found = chapter_dir(chapter)
        if found:
            chapter_paths.append(found)
    source = entry.get('source')
    if source:
        chapter_paths.append(str(Path(source).parent) if source.endswith('chapter.qmd') else source)
    inputs.paths.extend(chapter_paths)
    if entry['tool'] == 'pbi':
        inputs.paths.extend(['scripts/companion/pbibuild/schemas', 'facts/instructor/dax-markers-4feb03f.json'])
    return inputs.merged(companion_base_inputs())


def companion_units(manifest: dict) -> dict[str, list[Unit]]:
    chains = {c['id']: c for c in manifest['chains']}
    build = 'scripts/companion/build.py'
    units: dict[str, list[Unit]] = {'sql': [], 'excel': [], 'pbi': []}
    downstream = DOWNSTREAM['companion']

    pbi_chains = [c for c in manifest['chains'] if c['tool'] == 'pbi']
    for chain in manifest['chains']:
        tool = chain['tool']
        if tool == 'pbi':
            continue
        first = chain_chapters(chain)[0]
        units[tool].append(Unit(
            key=f'chain:{chain["id"]}', stage=f'companion-{tool}', title=f'{chain["file"]}, start files of the tutorials',
            commands=[[PY, build, '--tool', tool, '--chapter', str(first)]],
            inputs=entry_inputs(chain, manifest, chains), outputs=chain_outputs(chain, manifest),
            office='excel' if tool == 'excel' else None, dirties=downstream))
    if pbi_chains:                       # one unit: each chain's build refreshes the other's copy of a checkpoint
        inputs = Inputs()
        outputs: list[str] = []
        for chain in pbi_chains:
            inputs = inputs.merged(entry_inputs(chain, manifest, chains))
            outputs.extend(chain_outputs(chain, manifest))
        inputs.tokens = {'entries': json.dumps(pbi_chains, sort_keys=True, default=str),
                         'folders': f'{manifest["start_folder"]}/{manifest["solutions_folder"]}'}
        units['pbi'].append(Unit(
            key='chains:' + '+'.join(c['id'] for c in pbi_chains), stage='companion-pbi',
            title='Power BI reports and audit monitoring files, start files of the tutorials',
            commands=[[PY, build, '--tool', 'pbi', '--chapter', str(chain_chapters(c)[0])] for c in pbi_chains],
            inputs=inputs, outputs=tuple(outputs), office='pbi', dirties=downstream))
    for entry in manifest.get('solutions', []):
        tool = entry['tool']
        units[tool].append(Unit(
            key=f'solution:{entry["id"]}', stage=f'companion-{tool}', title=entry.get('file') or f'{entry["id"]} (SQL scripts)',
            commands=[[PY, build, '--solutions', '--id', entry['id']]],
            inputs=entry_inputs(entry, manifest, chains), outputs=(solution_output(entry, manifest),),
            office=tool if tool != 'sql' else None, dirties=downstream))
    return units


# --- The other stages -------------------------------------------------------------------------------------------------

def py(script: str, *args: str) -> list[str]:
    return [PY, script, *args]


def notes_inputs() -> Inputs:
    return Inputs(paths=['facts/notes', 'facts/db.py', 'scripts/facts.py', '_variables.yml'], sigs=list(DATASETS))


def instructor_paths() -> list[str]:
    """The parts of facts/instructor the guides and figures read: not facts/instructor/figures, which the figure build writes,
    and not the PDF layout, which only the PDF files use."""
    skip = {'figures', 'pdf', '__pycache__'}
    return sorted(rel(p) for p in (ROOT / 'facts/instructor').iterdir() if p.name not in skip)


def built_folders() -> list[str]:
    """The folders of built solution and start files that the guides and their figures open (the workbooks, projects and
    scripts inside), but not the Instructor-Notes package, which is made from the guides."""
    folders: list[str] = []
    for sub in ('solutions', 'start-files'):
        base = ROOT / COMPANION / sub
        if base.is_dir():
            folders.extend(rel(p) for p in sorted(base.iterdir()) if p.is_dir() and not p.name.startswith('Instructor-Notes'))
    return folders


def guide_inputs(figures_built: bool) -> Inputs:
    """What the guides and their figures read: templates, contexts, notes, the book's text and the built solution files."""
    inputs = Inputs(
        paths=[*instructor_paths(), 'facts/notes', 'facts/db.py', 'chapters', 'cases', 'appendices', 'scripts/figures',
               'scripts/companion', 'shared/calculations', '_variables.yml', 'index.qmd'],
        sigs=[*built_folders(), *DATASETS])
    if figures_built:                                   # render links a figure once its PDF exists
        inputs.paths.append('instructor-notes/figures')
    return inputs


def book_plan(ctx: Context, forced: bool) -> Plan:
    """The book, from the fingerprints scripts/build_all.py records (the ones release.py publish reads)."""
    tree = ctx.tree()
    recorded = release.load_fingerprints(ROOT)
    downloads = [ROOT / release.DOWNLOADS / f'book-latest.{ext}' for ext in release.BOOK_FORMATS]
    book_stale = (forced or recorded['book'] != release.fingerprint(ROOT, tree, release.inputs_of(ROOT, tree))
                  or not all(p.is_file() for p in downloads))
    decks = [deck for deck in release.deck_ids(ROOT)
             if forced or recorded['decks'].get(deck) != release.fingerprint(ROOT, tree, release.inputs_of(ROOT, tree, deck))
             or not (ROOT / release.PPTX / deck / f'{deck}.pptx').is_file()]
    if book_stale:
        return Plan([py('scripts/build_all.py')], 'forced' if forced else 'the book changed (renders the decks and the site too)')
    if not decks:
        return Plan([], 'current')
    if len(decks) > 6:
        return Plan([py('scripts/build_all.py', '--slides-only')], f'{len(decks)} decks changed')
    return Plan([py('scripts/build_all.py', '--slides-only', '--chapter', deck) for deck in decks],
                'decks changed: ' + ', '.join(decks))


def package_plan(ctx: Context, forced: bool) -> Plan:
    package = ROOT / COMPANION / 'solutions/Instructor-Notes.zip'
    pdfs = list((ROOT / 'outputs/instructor/pdf').rglob('*.pdf'))
    command = [py('facts/instructor/guides.py', 'package')]
    if forced:
        return Plan(command, 'forced')
    if not package.is_file():
        return Plan(command, 'Instructor-Notes.zip is missing')
    newest = max((p.stat().st_mtime for p in pdfs), default=0)
    if newest > package.stat().st_mtime:
        return Plan(command, 'a PDF file is newer than Instructor-Notes.zip')
    return Plan([], 'current')


PRINT_INPUTS = Inputs(paths=[*release.BOOK_INPUTS, 'print', 'scripts/print', '_quarto-print-color.yml', '_quarto-print-bw.yml'])


def print_snapshot(ctx: Context, fresh: bool = False) -> dict[str, str]:
    snap = snapshot(PRINT_INPUTS, ctx.tree(fresh=fresh))
    snap['token:draft'] = str(isbn_blank())            # a draft and a final interior differ
    return snap


def print_plan(ctx: Context, forced: bool) -> Plan:
    snap = print_snapshot(ctx)
    record = ctx.store['units'].get('print/interiors')
    command = [py('scripts/print/build.py', *(['--draft'] if isbn_blank() else []))]
    outputs = ['outputs/print/*_Print_Color*.pdf', 'outputs/print/*_Print_BW*.pdf']
    again = lambda c: print_snapshot(c, fresh=True)                      # noqa: E731
    if forced:
        return Plan([command], 'forced', snap, again)
    if record is None:
        return Plan([command], 'not recorded as built', snap, again)
    if any(not output_exists(o) for o in outputs):
        return Plan([command], 'a print PDF is missing', snap, again)
    diff = changes(record['snapshot'], snap)
    if diff:
        return Plan([command], 'changed: ' + ', '.join(diff[:3]), snap, again)
    return Plan([], 'current', snap, again)


def isbn_blank() -> bool:
    import yaml
    isbn = (yaml.safe_load((ROOT / '_quarto.yml').read_text(encoding='utf-8')) or {}).get('isbn') or {}
    return not (isbn.get('paperback-color') and isbn.get('paperback-bw'))


def publish_plan_for(dry_run: bool) -> Callable[[Context, bool], Plan]:
    def plan(ctx: Context, forced: bool) -> Plan:
        dirty = release.git(ROOT, 'status', '--porcelain', '--untracked-files=all')
        if dirty and not dry_run:
            raise ValueError('Commit the changes first: a revision is published from a commit. Then run this command again '
                             'with --publish (nothing is rebuilt if it is current).\n' + dirty[:1500])
        return Plan([py('scripts/release.py', 'publish', *(['--dry-run'] if dry_run else []))],
                    'publish --dry-run' if dry_run else 'publish')
    return plan


def build_stages(args: argparse.Namespace) -> list[Stage]:
    import yaml
    manifest = yaml.safe_load(MANIFEST.read_text(encoding='utf-8'))
    companion = companion_units(manifest)
    figure_sources = Inputs(paths=list(closure(('scripts/figures/build.py',))) + ['shared/calculations', '_variables.yml'],
                            sigs=list(DATASETS))
    stages = {
        'gates': [Unit('fast-checks', 'gates', 'keys, literals, citation file, deck sources, SQL, quick reference, competency map',
                       commands=[py('scripts/verify/var_keys_check.py'), py('facts/phase7_cli.py', 'lint'),
                                 py('scripts/citation_cff.py', '--check'), py('scripts/build_all.py', '--check'),
                                 py('scripts/verify/quick_reference_check.py'), py('scripts/verify/competency_map_check.py'),
                                 py('scripts/verify/sql_check.py'), py('scripts/verify/tutorial_queries_check.py')],
                       always=True)],
        'figures': [
            Unit('sources', 'figures', 'the generated figure sources (visuals/src)', [py('scripts/figures/build.py')],
                 inputs=figure_sources, outputs=('visuals/src',), dirties=DOWNSTREAM['figures-sources']),
            Unit('export', 'figures', 'the SVG and PDF exports (incremental by checksum)', [py('scripts/export_drawio_svgs.py')],
                 always=True),
            Unit('standard', 'figures', 'the figure standard', [py('scripts/figures/check_figures.py')], always=True)],
        'companion-sql': companion['sql'], 'companion-excel': companion['excel'], 'companion-pbi': companion['pbi'],
        'instructor-figures': [Unit(
            'build', 'instructor-figures', 'the 240 instructor figures (PDF and Draw.io source)',
            [py('scripts/figures/instructor/build_instructor.py'),
             py('scripts/figures/instructor/build_instructor.py', '--verify', '--complete'),
             py('scripts/figures/check_figures.py', '--src-dir', 'facts/instructor/figures')],
            inputs=guide_inputs(figures_built=False), outputs=('instructor-notes/figures/manifest.json',),
            dirties=DOWNSTREAM['instructor-figures'])],
        'guides': [Unit(
            'render-check', 'guides', 'render every guide from its template, then check them',
            [py('facts/instructor/guides.py', 'render', '--all'), py('facts/instructor/guides.py', 'check', '--all')],
            inputs=guide_inputs(figures_built=True), outputs=('instructor-notes/README.md',), retries=1,
            dirties=DOWNSTREAM['guides'])],
        'instructor-pdf': [
            Unit('pdf', 'instructor-pdf', 'the guides as PDF files (incremental by content)',
                 [py('facts/instructor/guides.py', 'pdf', '--all')], always=True),
            Unit('instructor-package', 'instructor-pdf', 'Instructor-Notes.zip (PDF files only)', custom=package_plan)],
        'supplementary': [Unit('copy', 'supplementary', 'copy the built files into supplementary/ and check them against the '
                               'Downloads page', [py('scripts/companion/build.py', '--publish')], always=True)],
        'book': [Unit('book-and-decks', 'book', 'the PDF, EPUB, DOCX, both deck formats and the site', custom=book_plan)],
        'print': [Unit('interiors', 'print', 'the print interiors (color and black and white)', custom=print_plan)],
        'checks': [
            Unit('notes', 'checks', 'every generated note against the data',
                 [py('scripts/facts.py', 'check')], inputs=notes_inputs(), outputs=()),
            Unit('unit-tests', 'checks', 'the unit tests',
                 # -b: a passing test's output (the release tests print the warnings of a fake revision) stays out of the log
                 [[PY, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-b']], always=True)],
        'publish': [Unit('release', 'publish', 'scripts/release.py publish',
                         custom=publish_plan_for(bool(args.publish_dry_run) and not args.publish))],
    }
    return [Stage(name, stages[name]) for name in STAGE_ORDER]


# --- Selecting what runs ----------------------------------------------------------------------------------------------

def matches(unit: Unit, names: list[str]) -> bool:
    return any(name in ('all', unit.stage, unit.key, unit.name) or unit.name.startswith(name + '/') for name in names)


def select_units(stages: list[Stage], args: argparse.Namespace) -> list[Unit]:
    names = [s.name for s in stages]
    known = {u.name for s in stages for u in s.units} | {u.key for s in stages for u in s.units} | set(names) | {'all'}
    for option in (args.only or []) + (args.skip or []) + (args.force or []):
        if option not in known:
            raise ValueError(f'Unknown stage or unit: {option} (python scripts/build_everything.py --list)')
    if args.from_stage and args.from_stage not in names:
        raise ValueError(f'Unknown stage: {args.from_stage}')
    start = names.index(args.from_stage) if args.from_stage else 0
    chosen: list[Unit] = []
    for index, stage in enumerate(stages):
        if index < start:
            continue
        opted = (stage.name == 'print' and args.print) or (stage.name == 'publish' and (args.publish or args.publish_dry_run))
        if stage.name in OPT_IN and not opted and not (args.only and matches_stage(stage, args.only)):
            continue
        for unit in stage.units:
            if args.only and not matches(unit, args.only):
                continue
            if args.skip and matches(unit, args.skip):
                continue
            chosen.append(unit)
    return chosen


def matches_stage(stage: Stage, names: list[str]) -> bool:
    return any(stage.name == n or any(matches(u, [n]) for u in stage.units) for n in names)


# --- Running ----------------------------------------------------------------------------------------------------------

def office_problem(tool: str) -> str | None:
    if platform.system() != 'Windows':
        return 'The Excel and Power BI Desktop builds need Windows.'
    if tool != 'excel':
        return None
    try:
        import openpyxl  # noqa: F401
        import win32com.client  # noqa: F401
    except ImportError as exc:
        return f'{exc}. Install scripts/companion/requirements-excel.txt in the environment that runs this script.'
    return None


def shown(command: list[str]) -> str:
    return ' '.join(['python' if part == PY else part for part in command])


def run_command(command: list[str], log) -> tuple[int, str]:
    print('+ ' + shown(command), flush=True)
    log.write('+ ' + shown(command) + '\n')
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    tail: collections.deque[str] = collections.deque(maxlen=80)
    with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding='utf-8', errors='replace', env=env, bufsize=1) as process:
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            log.write(line)
            tail.append(line)
        sys.stdout.flush()
        code = process.wait()
    return code, ''.join(tail)


def load_store() -> dict:
    data = json.loads(STORE.read_text(encoding='utf-8')) if STORE.is_file() else {}
    return {'units': dict(data.get('units') or {})}


def save_store(store: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(store, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours}h{minutes:02d}m' if hours else f'{minutes}m{secs:02d}s' if minutes else f'{secs}s'


@dataclass
class Result:
    unit: Unit
    status: str          # built | current | skipped | planned | failed
    detail: str = ''
    seconds: float = 0.0


def run_units(units: list[Unit], args: argparse.Namespace) -> list[Result]:
    store = load_store()
    ctx = Context(store)
    results: list[Result] = []
    dirty: set[str] = set()                              # --plan: what earlier units would make out of date
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = None if args.plan else LOG.open('w', encoding='utf-8')
    if log:
        log.write(f'build_everything {dt.datetime.now().isoformat(timespec="seconds")}\n')
    current_stage = None
    try:
        for unit in units:
            if unit.stage != current_stage:
                current_stage = unit.stage
                print(f'\n== {unit.stage}: {STAGE_TITLES.get(unit.stage, unit.stage)} ==', flush=True)
                ctx.tree(fresh=not args.plan and bool(results))      # an earlier stage may have changed tracked files
            forced = bool(args.force) and matches(unit, args.force)
            if unit.office and args.no_office:
                results.append(Result(unit, 'skipped', '--no-office'))
                print(f'  skip  {unit.key}  (--no-office)')
                continue
            try:
                plan = plan_unit(unit, ctx, forced)
            except ValueError as exc:
                results.append(Result(unit, 'failed', str(exc)))
                print(f'  FAIL  {unit.key}: {exc}')
                break
            upstream = args.plan and (unit.stage in dirty or unit.key in dirty)
            if not plan.commands and not upstream:
                results.append(Result(unit, 'current', plan.reason))
                print(f'  ok    {unit.key}  (current)')
                continue
            reason = plan.reason if plan.commands else 'files it reads will be rebuilt above'
            if args.plan:
                if unit.always:
                    results.append(Result(unit, 'always', reason))
                    print(f'  run   {unit.key}  ({reason})')
                else:
                    dirty.update(unit.dirties)
                    results.append(Result(unit, 'planned', reason))
                    print(f'  RUN   {unit.key}  ({reason})')
                continue
            if unit.office:
                problem = office_problem(unit.office)
                if problem:
                    results.append(Result(unit, 'failed', problem))
                    print(f'  FAIL  {unit.key}: {problem}\n        Use --no-office to leave these builds out.')
                    break
            print(f'  RUN   {unit.key}: {unit.title}  ({reason})', flush=True)
            started = time.time()
            ok = True
            for command in plan.commands:
                code, tail = run_command(command, log)
                attempts = unit.retries
                while code and attempts and RETRY_ON in tail:
                    attempts -= 1
                    print(f'  (the step failed with "{RETRY_ON}", an intermittent Windows error: running it again)', flush=True)
                    code, tail = run_command(command, log)
                if code:
                    ok = False
                    results.append(Result(unit, 'failed', f'{shown(command)} exited with {code}', time.time() - started))
                    break
            if not ok:
                break
            record_unit(unit, plan, ctx)
            results.append(Result(unit, 'built', reason, time.time() - started))
            print(f'  done  {unit.key} in {duration(time.time() - started)}', flush=True)
    finally:
        if log:
            log.close()
    return results


def record_unit(unit: Unit, plan: Plan, ctx: Context) -> None:
    """Record what the unit was built from, unless its own inputs changed while it ran."""
    if plan.snapshot is None or plan.recompute is None:
        return
    after = plan.recompute(ctx)
    if after != plan.snapshot:
        print(f'  WARNING: the inputs of {unit.key} changed while it was built ({", ".join(changes(plan.snapshot, after)[:3])}), '
              'so it is not recorded as current; run the command again.', flush=True)
        return
    ctx.store['units'][unit.name] = {'snapshot': after, 'built': dt.datetime.now().isoformat(timespec='seconds')}
    save_store(ctx.store)


# --- --adopt ----------------------------------------------------------------------------------------------------------

def adopt(units: list[Unit], trust: bool, ignore: list[str]) -> int:
    """Record the files that exist as built from the current sources, for the units that have inputs. An output older
    than one of its inputs is refused, unless the input is named in ignore (a change you know leaves the output as it is)."""
    skip = {Path(name).as_posix() for name in ignore}
    store = load_store()
    ctx = Context(store)
    adopted = refused = 0
    for unit in units:
        if unit.inputs is None or unit.always or unit.custom:
            continue
        gone = missing_outputs(unit)
        if gone:
            print(f'  no    {unit.name}: {gone[0]} does not exist')
            refused += 1
            continue
        outputs = [p for pattern in unit.outputs for p in (ROOT.glob(pattern) if any(c in pattern for c in '*?[')
                                                            else [ROOT / pattern])]
        if not unit.outputs and not trust:
            print(f'  no    {unit.name}: it has no output to compare with (adopt it with --trust if it passed)')
            refused += 1
            continue
        output_time = min((p.stat().st_mtime for p in outputs), default=0)
        newer = [] if trust else sorted(rel(f) for f in input_files(unit.inputs)
                                        if f.stat().st_mtime > output_time and rel(f) not in skip)
        if newer:
            more = f' and {len(newer) - 1} more' if len(newer) > 1 else ''
            print(f'  no    {unit.name}: {newer[0]}{more} newer than the output (build it, or --ignore-newer)')
            refused += 1
            continue
        store['units'][unit.name] = {'snapshot': snapshot(unit.inputs, ctx.tree()),
                                     'built': dt.datetime.now().isoformat(timespec='seconds'), 'adopted': True}
        print(f'  ok    {unit.name}')
        adopted += 1
    save_store(store)
    print(f'\nAdopted {adopted} unit(s), refused {refused}.')
    return 0


# --- The command line -------------------------------------------------------------------------------------------------

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--plan', action='store_true', help='show what would run and why; run nothing')
    p.add_argument('--list', action='store_true', help='list the stages and their units')
    p.add_argument('--only', nargs='+', metavar='NAME', help='run only these stages or units')
    p.add_argument('--skip', nargs='+', metavar='NAME', help='leave these stages or units out')
    p.add_argument('--from', dest='from_stage', metavar='STAGE', help='start at this stage')
    p.add_argument('--force', nargs='+', metavar='NAME', help='run these stages or units even if current (all for everything)')
    p.add_argument('--no-office', action='store_true', help='leave out the Excel and Power BI Desktop builds')
    p.add_argument('--print', action='store_true', help='also build the print interiors')
    p.add_argument('--publish', action='store_true', help='then run scripts/release.py publish (needs a clean, committed main)')
    p.add_argument('--publish-dry-run', action='store_true', help='then run scripts/release.py publish --dry-run')
    p.add_argument('--adopt', action='store_true', help='record existing files as built from the current sources')
    p.add_argument('--trust', action='store_true', help='with --adopt: do not compare file times at all')
    p.add_argument('--ignore-newer', nargs='+', default=[], metavar='PATH',
                   help='with --adopt: inputs that are newer than an output but do not change it')
    return p


def list_stages(stages: list[Stage]) -> None:
    for stage in stages:
        print(f'{stage.name}{"  (opt-in)" if stage.name in OPT_IN else ""}: {STAGE_TITLES[stage.name]}')
        for unit in stage.units:
            marks = ' [Excel]' if unit.office == 'excel' else ' [Power BI Desktop]' if unit.office == 'pbi' else ''
            print(f'    {unit.key}{marks}')


def summarize(results: list[Result], elapsed: float, args: argparse.Namespace) -> int:
    counts = collections.Counter(r.status for r in results)
    print('\n' + '=' * 78)
    if args.plan:
        print(f'Plan: {counts["planned"]} to run, {counts["current"]} current, {counts["skipped"]} skipped, '
              f'{counts["always"]} cheap checks that run every time.')
        if counts['planned']:
            print('Run it with: python scripts/build_everything.py')
        return 0
    for r in results:
        if r.status == 'built':
            print(f'  built   {r.unit.name}  ({duration(r.seconds)})')
    failed = [r for r in results if r.status == 'failed']
    for r in failed:
        print(f'  FAILED  {r.unit.name}: {r.detail}')
    print(f'Built {counts["built"]}, current {counts["current"]}, skipped {counts["skipped"]}, failed {counts["failed"]} '
          f'in {duration(elapsed)}. Log: {rel(LOG)}')
    if failed:
        print('Fix the cause and run the command again: the finished units are skipped.')
        return 1
    dirty = release.git(ROOT, 'status', '--porcelain')
    if dirty and not (args.publish and not args.publish_dry_run):
        print('\nThe working tree has uncommitted changes (the build may have changed tracked files). To publish: review them,\n'
              'commit, then run\n    python scripts/build_everything.py --publish\n'
              '(the commit leaves every unit current, so it only runs the cheap checks and publishes).')
    elif not args.publish:
        print('\nNothing to commit. Publish with: python scripts/build_everything.py --publish')
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    args = parser().parse_args(argv)
    try:
        stages = build_stages(args)
        if args.list:
            list_stages(stages)
            return 0
        units = select_units(stages, args)
        if args.adopt:
            return adopt(units, args.trust, args.ignore_newer)
        started = time.time()
        results = run_units(units, args)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nInterrupted. Run the command again: the finished units are skipped.', file=sys.stderr)
        return 130
    return summarize(results, time.time() - started, args)


if __name__ == '__main__':
    raise SystemExit(main())
