#!/usr/bin/env python3
"""Publish a revision of the book as a GitHub release, and check that release from GitHub Actions.

GitHub Actions renders the site: the book's HTML and the Reveal decks. The files the site links but does not serve
are built locally and published as the assets of the revision's release (the book block of _variables.yml): the PDF,
EPUB and DOCX, a PowerPoint file per deck, and the companion and solution files. filters/slide-links.lua points the
links at the release. A new revision is a new tag and release; publishing the same revision again uploads only the
files that changed. The release's text is a page in the manner of the book's Downloads page: links to the book,
the dataset, and the slides, companion and solution files by chapter, written by publish (or by notes).

  python scripts/release.py status                    what is built, current, and on the release
  python scripts/release.py publish [--dry-run]       build what is stale, upload what changed, push main
  python scripts/release.py notes [--update]          write the release page (--update puts it on the release)
  python scripts/release.py bump 2027.2               start a new revision (then commit _variables.yml)
  python scripts/release.py check --site _book        GitHub Actions: the release holds every file the site links

The book and deck files are compared by what they were built from (a fingerprint of their input paths), because a
rebuild changes their bytes; the companion files are compared by SHA-256. publish needs the GitHub CLI, signed in.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = 'outputs/build/downloads'      # the local build's book-latest.{pdf,epub,docx}
PPTX = 'slides/_build/pptx'                # the local build's <deck>/<deck>.pptx
SUPPLEMENTARY = 'supplementary'            # the companion and solution files (gitignored; companion/build.py --publish)
FINGERPRINTS = 'outputs/build/fingerprints.json'
STAGE = 'outputs/release'                  # the files to upload, under their names on the release
MANIFEST = 'manifest.json'
WORKFLOW = 'publish.yml'
BOOK_FORMATS = ('pdf', 'epub', 'docx')
BUILT = ('book', 'deck')                   # the kinds compared by fingerprint
# What the built files are made from. A fingerprint holds the git object of each input path, so a file is out of
# date exactly when one of them changed after it was built.
BOOK_INPUTS = ('_quarto.yml', '_variables.yml', 'index.qmd', 'front-matter', 'chapters', 'cases', 'appendices',
               'back-matter', 'shared/fragments', 'visuals', 'styles', 'filters')
DECK_INPUTS = ('_variables.yml', 'slides/_quarto.yml', 'slides/theme', 'slides/shortcodes', 'slides/filters',
               'filters/strip-comments.lua', 'scripts/slides', 'shared/fragments', 'visuals/src', 'visuals/svg')
BOOK_SOURCES = ('index.qmd', 'front-matter', 'chapters', 'cases', 'appendices', 'back-matter', 'shared/fragments')
SOURCE_LINK = re.compile(r'\]\((/(?:downloads|supplementary)/[^)\s]+)\)')
HREF = re.compile(r'href="([^"]*)"')
# The release page (release_notes): the book's website shows the newest text; the Downloads page's table is read for
# the rows; the dataset files are the three the Downloads page links (the key is the one of dataset.sha256).
SITE = 'https://aa.accountinganalyticshub.com'
DATASET_SITE = 'https://charlesriver.accountinganalyticshub.com/'
DOWNLOADS_PAGE = 'front-matter/downloads.qmd'
INSTRUCTOR_NOTES = 'Instructor-Notes.zip'
TABLE_LINK = re.compile(r'\[([^\]]+)\]\((/supplementary/[^)\s]+)\)')
DECK_ATTRIBUTE = re.compile(r'data-chapter="([^"]+)"')
DATASET_FILES = (('sqlite', 'SQLite', 'CharlesRiver.sqlite', 'The SQL chapters, in DB Browser for SQLite'),
                 ('xlsx', 'Excel', 'CharlesRiver.xlsx', 'The Excel and Power BI chapters'),
                 ('csv', 'CSV package', 'CharlesRiver_csv.zip', 'The same tables as plain CSV files'))


# --- The revision ---------------------------------------------------------------------------------------------------

class Revision:
    """The book block of _variables.yml: the edition, the revision, its tag, and the URLs of its release."""

    def __init__(self, revision: str, tag: str, release: str, download: str, edition: str = 'first'):
        self.revision, self.tag, self.release, self.download = revision, tag, release, download.rstrip('/')
        self.edition = edition
        match = re.fullmatch(r'https://github\.com/([\w.-]+/[\w.-]+)/releases/tag/(.+)', release)
        if not match or match.group(2) != tag:
            raise ValueError(f'_variables.yml: book.release must be the release page of book.tag ({tag}): {release}')
        self.repo = match.group(1)
        if self.download != f'https://github.com/{self.repo}/releases/download/{tag}':
            raise ValueError(f'_variables.yml: book.download must be the download address of book.tag ({tag}): '
                             f'{download}')

    def url(self, name: str) -> str:
        return f'{self.download}/{urllib.parse.quote(name)}'

    @property
    def title(self) -> str:
        """The release's title, such as "First edition, revision 2027.1"."""
        return f'{self.edition[:1].upper()}{self.edition[1:]} edition, revision {self.revision}'

    @property
    def book_name(self) -> str:
        """The name of the PDF, EPUB and DOCX on the release, without the extension, from the edition and the
        revision: Accounting_Analytics_First_Edition_Rev_2027_1. filters/slide-links.lua builds the same name."""
        words = ''.join(f'{word[:1].upper()}{word[1:]}_' for word in re.split(r'[\s_-]+', self.edition) if word)
        return f'Accounting_Analytics_{words}Edition_Rev_{re.sub(r"[^0-9A-Za-z]+", "_", self.revision)}'


def read_revision(root: Path) -> Revision:
    import yaml
    data = yaml.safe_load((root / '_variables.yml').read_text(encoding='utf-8')) or {}
    book = data.get('book') or {}
    for key in ('edition', 'revision', 'tag', 'release', 'download'):
        if not book.get(key):
            raise ValueError(f'_variables.yml: book.{key} is missing')
    return Revision(str(book['revision']), str(book['tag']), str(book['release']), str(book['download']),
                    str(book['edition']))


def bump(root: Path, revision: str) -> Revision:
    """Point the book block at a new revision; its release is created by the next publish."""
    if not re.fullmatch(r'\d{4}\.\d+', revision):
        raise ValueError(f'A revision is a year and a number, such as 2027.2: {revision}')
    current = read_revision(root)
    tag = f'book-v{revision}'
    values = {'revision': revision, 'tag': tag,
              'release': f'https://github.com/{current.repo}/releases/tag/{tag}',
              'download': f'https://github.com/{current.repo}/releases/download/{tag}'}
    path = root / '_variables.yml'
    with open(path, encoding='utf-8', newline='') as handle:
        text = handle.read()
    block = re.search(r'^book:[ \t]*\r?\n((?:[ \t]+[^\r\n]*\r?\n|\r?\n)*)', text, re.M)
    if block is None:
        raise ValueError('_variables.yml has no book block')
    body = block.group(1)
    for key, value in values.items():
        body, count = re.subn(rf'^([ \t]+{key}:[ \t]*)[^\r\n]*', lambda m, v=value: f'{m.group(1)}"{v}"', body,
                              count=1, flags=re.M)
        if not count:
            raise ValueError(f'_variables.yml: no book.{key} line')
    with open(path, 'w', encoding='utf-8', newline='') as handle:
        handle.write(text[:block.start(1)] + body + text[block.end(1):])
    return read_revision(root)


# --- Git and fingerprints -------------------------------------------------------------------------------------------

def git(root: Path, *args: str, env: dict | None = None, stdin: str | None = None) -> str:
    result = subprocess.run(['git', *args], cwd=root, env=env, input=stdin, capture_output=True, text=True,
                            encoding='utf-8', check=False)
    if result.returncode:
        raise RuntimeError(f'git {" ".join(args)} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def working_tree(root: Path) -> str:
    """The tree a commit of the working tree would have now: tracked and untracked files, .gitignore applied."""
    index = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-path', 'index'))
    with tempfile.TemporaryDirectory() as temp:
        copy = Path(temp) / 'index'
        if index.is_file():
            shutil.copyfile(index, copy)
        env = {**os.environ, 'GIT_INDEX_FILE': str(copy)}
        git(root, 'add', '--all', env=env)
        return git(root, 'write-tree', env=env)


def head_tree(root: Path) -> str:
    return git(root, 'rev-parse', 'HEAD^{tree}')


def inputs_of(root: Path, tree: str, deck: str | None = None) -> list[str]:
    """The input paths of the book's PDF, EPUB and DOCX, or of one deck (with its own chapter's folder, or a
    comprehensive case's page)."""
    if deck is None:
        return list(BOOK_INPUTS)
    case = re.fullmatch(r'case-part-(\d)', deck)
    if case:
        return [*DECK_INPUTS, f'slides/{deck}', f'cases/part-{case.group(1)}-case.qmd']
    number = deck.split('-')[1]
    chapters = [path for path in git(root, 'ls-tree', '--name-only', tree, 'chapters/').splitlines()
                if path.rsplit('/', 1)[-1].startswith(number + '-')]
    return [*DECK_INPUTS, f'slides/{deck}', *chapters]


def fingerprint(root: Path, tree: str, paths: list[str]) -> dict[str, str]:
    """The git object of each path in the tree ('' for a path the tree lacks)."""
    lines = git(root, 'cat-file', '--batch-check=%(objectname)', stdin=''.join(f'{tree}:{p}\n' for p in paths))
    objects = lines.splitlines()
    if len(objects) != len(paths):
        raise RuntimeError('git cat-file returned an unexpected listing')
    return {path: ('' if line.endswith(' missing') else line) for path, line in zip(paths, objects)}


def changed_inputs(built: dict, current: dict) -> list[str]:
    return sorted(path for path in set(built) | set(current) if built.get(path) != current.get(path))


def source_tree(root: Path) -> str | None:
    """What a local build starts from, or None when this is not a git checkout (no fingerprints are recorded)."""
    try:
        return working_tree(root)
    except (OSError, RuntimeError):
        return None


def load_fingerprints(root: Path) -> dict:
    path = root / FINGERPRINTS
    data = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    return {'book': data.get('book'), 'decks': dict(data.get('decks') or {})}


def record_build(root: Path, tree: str | None, *, book: bool, decks: list[str]) -> None:
    """After a local build: record what its files were built from, so release.py knows they are current."""
    if tree is None:
        return
    after = source_tree(root)
    if after is None:
        return
    # A file is recorded only if its own inputs did not change while it was being built; an edit elsewhere
    # (a README, a test) does not make the build's files out of date.
    data, recorded, changed = load_fingerprints(root), 0, []
    for deck in ([None] if book else []) + list(decks):
        built = fingerprint(root, tree, inputs_of(root, tree, deck))
        if fingerprint(root, after, inputs_of(root, after, deck)) != built:
            changed.append(deck or 'the book (PDF, EPUB, DOCX)')
            continue
        if deck is None:
            data['book'] = built
        else:
            data['decks'][deck] = built
        recorded += 1
    if changed:
        print(f'WARNING: the sources of {", ".join(changed)} changed during the build, so those files are not '
              'recorded as current; build them again before publishing.', flush=True)
    if recorded:
        path = root / FINGERPRINTS
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


# --- The files of a revision ----------------------------------------------------------------------------------------

class Asset:
    def __init__(self, name: str, kind: str, path: Path, deck: str | None = None):
        self.name, self.kind, self.path, self.deck = name, kind, path, deck


# A chapter's deck (chapter-01) or a comprehensive case's (case-part-1), as scripts/slides/book_index.DECK_GLOBS.
DECK_GLOBS = ('chapter-[0-9][0-9]', 'case-part-[0-9]')


def deck_ids(root: Path) -> list[str]:
    return sorted(path.parent.name for pattern in DECK_GLOBS for path in (root / 'slides').glob(f'{pattern}/index.qmd'))


def asset_name(target: str, revision: Revision) -> str:
    """The release name of a file the book links by root path; filters/slide-links.lua maps links the same way."""
    match = re.fullmatch(r'/downloads/book-latest\.(\w+)', target)
    if match and match.group(1) in BOOK_FORMATS:
        return f'{revision.book_name}.{match.group(1)}'
    if target.startswith('/supplementary/') and not target.endswith('/'):
        return target.rsplit('/', 1)[-1]
    raise ValueError(f'The book links {target}, which is not a release file '
                     f'(only /downloads/book-latest.{{{",".join(BOOK_FORMATS)}}} and /supplementary/...)')


def source_links(root: Path) -> list[str]:
    links = []
    for entry in BOOK_SOURCES:
        path = root / entry
        for page in ([path] if path.is_file() else sorted(path.rglob('*.qmd'))):
            links += SOURCE_LINK.findall(page.read_text(encoding='utf-8'))
    return links


def expected_assets(root: Path, revision: Revision | None = None) -> dict[str, Asset]:
    """Every file the revision's release must hold: the book, one PowerPoint file per deck, the companion files."""
    revision = revision or read_revision(root)
    book = revision.book_name
    assets = {f'{book}.{ext}': Asset(f'{book}.{ext}', 'book', root / DOWNLOADS / f'book-latest.{ext}')
              for ext in BOOK_FORMATS}
    for deck in deck_ids(root):
        assets[f'{deck}.pptx'] = Asset(f'{deck}.pptx', 'deck', root / PPTX / deck / f'{deck}.pptx', deck)
    for target in source_links(root):
        name = asset_name(target, revision)
        if not target.startswith('/supplementary/'):
            continue
        path = root / SUPPLEMENTARY / target[len('/supplementary/'):]
        if name in assets and assets[name].path != path:
            raise ValueError(f'Two files would have the same name on the release: {name}')
        assets[name] = Asset(name, 'companion', path)
    return assets


def site_links(site: Path, revision: Revision) -> set[str]:
    """The release files the rendered site links."""
    prefix = revision.download + '/'
    names = set()
    for page in site.rglob('*.html'):
        for href in HREF.findall(page.read_text(encoding='utf-8', errors='replace')):
            href = html.unescape(href)
            if href.startswith(prefix):
                names.add(urllib.parse.unquote(href[len(prefix):]))
    return names


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def megabytes(size: int) -> str:
    return f'{size / 1_000_000:.1f} MB'


# --- The release, through the GitHub CLI ----------------------------------------------------------------------------

class GitHub:
    """The revision's release, read and written with the GitHub CLI (gh)."""

    def __init__(self, repo: str):
        self.repo = repo

    def gh(self, *args: str, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(['gh', *args], capture_output=capture, text=True, encoding='utf-8', check=False)
        except FileNotFoundError:
            raise RuntimeError('The GitHub CLI is not installed: winget install --id GitHub.cli, then gh auth login'
                               ) from None
        if check and result.returncode:
            detail = (result.stderr or result.stdout or '').strip() if capture else ''
            raise RuntimeError(f'gh {" ".join(args[:2])} failed{": " + detail if detail else ""}')
        return result

    def authenticated(self) -> None:
        self.gh('auth', 'status')

    def release(self, tag: str) -> dict | None:
        result = self.gh('release', 'view', tag, '--repo', self.repo, '--json', 'assets,url', check=False)
        if result.returncode:
            if 'not found' in (result.stderr + result.stdout).lower():
                return None
            raise RuntimeError(f'gh release view failed: {result.stderr.strip()}')
        return json.loads(result.stdout)

    def manifest(self, tag: str) -> dict | None:
        with tempfile.TemporaryDirectory() as temp:
            result = self.gh('release', 'download', tag, '--repo', self.repo, '--pattern', MANIFEST, '--dir', temp,
                             check=False)
            path = Path(temp) / MANIFEST
            if result.returncode or not path.is_file():
                return None
            return json.loads(path.read_text(encoding='utf-8'))

    def create(self, tag: str, title: str, notes: Path) -> None:
        self.gh('release', 'create', tag, '--repo', self.repo, '--verify-tag', '--latest', '--title', title,
                '--notes-file', str(notes))

    def upload(self, tag: str, path: Path) -> None:
        self.gh('release', 'upload', tag, str(path), '--repo', self.repo, '--clobber', capture=False)

    def delete_asset(self, tag: str, name: str) -> None:
        self.gh('release', 'delete-asset', tag, name, '--repo', self.repo, '--yes')

    def edit_notes(self, tag: str, notes: Path) -> None:
        self.gh('release', 'edit', tag, '--repo', self.repo, '--notes-file', str(notes))

    def run_workflow(self, workflow: str, ref: str) -> None:
        self.gh('workflow', 'run', workflow, '--repo', self.repo, '--ref', ref)


# --- Freshness and the upload plan ----------------------------------------------------------------------------------

def stale_builds(root: Path, tree: str, assets: dict[str, Asset]) -> tuple[bool, list[str]]:
    """Whether the local book files, and which local decks, were not built from this tree."""
    recorded = load_fingerprints(root)
    book = [asset for asset in assets.values() if asset.kind == 'book']
    book_stale = (recorded['book'] != fingerprint(root, tree, inputs_of(root, tree))
                  or not all(asset.path.is_file() for asset in book))
    decks = [asset.deck for asset in assets.values() if asset.kind == 'deck'
             and (recorded['decks'].get(asset.deck) != fingerprint(root, tree, inputs_of(root, tree, asset.deck))
                  or not asset.path.is_file())]
    return book_stale, decks


def refresh(root: Path, tree: str, assets: dict[str, Asset], *, build: bool) -> None:
    """Build what is not current: the whole book (which renders every deck too), or only the stale decks."""
    book, decks = stale_builds(root, tree, assets)
    if not book and not decks:
        print('The local book and deck files were built from this commit.', flush=True)
        return
    names = (['the book (PDF, EPUB, DOCX)'] if book else []) + decks
    if not build:
        raise ValueError(f'Not built from this commit: {", ".join(names)}. Publish without --no-build, '
                         'or build with python scripts/build_all.py first.')
    print(f'Building: {", ".join(names)}', flush=True)
    # Only the release's files: no HTML or Reveal decks, which GitHub Actions renders with the site.
    commands = ([[sys.executable, 'scripts/build_all.py', '--release']] if book else
                [[sys.executable, 'scripts/build_all.py', '--release', '--slides-only', '--chapter', deck]
                 for deck in decks])
    for command in commands:
        print('+ ' + ' '.join(command), flush=True)
        subprocess.run(command, cwd=root, check=True)
    book, decks = stale_builds(root, tree, assets)
    if book or decks:
        changed = git(root, 'status', '--porcelain')
        raise RuntimeError('Still not current after building: ' + ', '.join((['the book'] if book else []) + decks)
                           + ('. The build changed tracked files (figure exports?); commit them and publish again:\n'
                              + changed if changed else ''))


def local_entry(asset: Asset, commit: str, recorded: dict) -> dict:
    entry = {'kind': asset.kind, 'size': asset.path.stat().st_size, 'sha256': sha256(asset.path), 'commit': commit}
    if asset.kind == 'book':
        entry['inputs'] = recorded['book']
    elif asset.kind == 'deck':
        entry['deck'] = asset.deck
        entry['inputs'] = recorded['decks'][asset.deck]
    return entry


def plan_uploads(entries: dict[str, dict], remote_names: set[str], remote_manifest: dict | None,
                 force: bool = False) -> tuple[list[str], list[str], dict[str, dict]]:
    """Which files to upload, which release files to delete, and the manifest entries of the files the release keeps.

    A book or deck file is uploaded when it was built from other inputs than the release's copy (a rebuild changes
    its bytes, not its content); a companion file when its SHA-256 differs; any file the release lacks."""
    remote = (remote_manifest or {}).get('assets') or {}
    uploads, kept = [], {}
    for name, entry in entries.items():
        previous = remote.get(name)
        if force or name not in remote_names or not previous:
            uploads.append(name)
            continue
        key = 'inputs' if entry['kind'] in BUILT else 'sha256'
        if previous.get(key) == entry[key] and previous.get('kind') == entry['kind']:
            kept[name] = previous
        else:
            uploads.append(name)
    deletes = sorted(remote_names - set(entries) - {MANIFEST})
    return uploads, deletes, kept


# --- The release page -----------------------------------------------------------------------------------------------
# The text of the release is built from the Downloads page (its Supplementary Material table, so the two stay in step),
# the dataset block of _variables.yml, and the release's own manifest, and it links only files the manifest lists.

class Row:
    """A row of the Downloads page's table: a chapter, a case or an appendix with its deck and its files (release
    names)."""

    def __init__(self, chapter: str, deck: str | None, companion: list[tuple[str, str]],
                 solutions: list[tuple[str, str]]):
        self.chapter, self.deck, self.companion, self.solutions = chapter, deck, companion, solutions


def downloads_rows(root: Path, revision: Revision | None = None) -> list[Row]:
    """The rows of the Supplementary Material table of front-matter/downloads.qmd, in the page's order."""
    path = root / DOWNLOADS_PAGE
    if not path.is_file():
        return []
    revision = revision or read_revision(root)
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not (line.startswith('|') and line.endswith('|')):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if len(cells) != 4 or cells[1] == 'Slides' or set(cells[0]) <= set(':- '):
            continue
        deck = DECK_ATTRIBUTE.search(cells[1])
        links = [[(label, asset_name(target, revision)) for label, target in TABLE_LINK.findall(cell)]
                 for cell in cells[2:]]
        rows.append(Row(cells[0], deck.group(1) if deck else None, *links))
    return rows


def read_dataset(root: Path) -> dict | None:
    """The dataset block of _variables.yml (version, window, release, download, sha256), or None."""
    import yaml
    data = yaml.safe_load((root / '_variables.yml').read_text(encoding='utf-8')) or {}
    dataset = data.get('dataset') or {}
    return dataset if dataset.get('version') and dataset.get('download') else None


def release_notes(revision: Revision, commit: str, manifest: dict, *, rows: list[Row] | tuple = (),
                  dataset: dict | None = None) -> str:
    """The text of the revision's release page: the book, the dataset, the slides, companion and solution files by
    chapter (as the Downloads page lists them), and the checksums. GitHub shows the files themselves below it."""
    assets = manifest['assets']
    edition = f'{revision.edition[:1].upper()}{revision.edition[1:]} edition'
    repo = f'https://github.com/{revision.repo}'
    downloads = f'{SITE}/front-matter/downloads.html'
    used: set[str] = set()

    def link(label: str, name: str) -> str:
        used.add(name)
        return f'[{label}]({revision.url(name)})'

    def links(files: list[tuple[str, str]]) -> str:
        return ' · '.join(link(label, name) for label, name in files if name in assets) or '—'

    page = [
        '<p align="center">',
        f'  <a href="{SITE}/"><img src="{SITE}/visuals/cover/cover-web.png" width="220" '
        'alt="Cover of Accounting Analytics: An Integrated Approach"></a>',
        '</p>',
        '',
        '<h1 align="center">Accounting Analytics: An Integrated Approach</h1>',
        '',
        '<p align="center">',
        f'  <strong>{edition} · Revision {revision.revision}</strong><br>',
        '  Mauricio Codesso, Ph.D.',
        '</p>',
        '',
        '<p align="center">',
        f'  <a href="{SITE}/"><strong>Read the latest version online</strong></a> &nbsp;·&nbsp;',
        f'  <a href="{downloads}">Downloads page</a> &nbsp;·&nbsp;',
        f'  <a href="{repo}/releases/latest">Newest revision</a> &nbsp;·&nbsp;',
        f'  <a href="{repo}/releases">All revisions</a>',
        '</p>',
        '',
        f'> **Looking for the latest version?** [The book\'s website]({SITE}/) always shows the newest text. This page '
        f'holds the files of revision {revision.revision}, and each new revision of the book gets a release page of '
        f'its own: [the newest one is always here]({repo}/releases/latest).',
        '',
        '## 📖 The book',
        '',
        f'Download revision {revision.revision} of the book in the format you prefer. Every link on this page '
        'downloads a file of this revision.',
        '',
        '| Format | Best for | Size |',
        '|:--|:--|--:|']
    for ext, icon, label, use in (('pdf', '📄', 'PDF', 'Reading on a screen, and printing'),
                                  ('epub', '📱', 'EPUB', 'E-readers, tablets, and phones'),
                                  ('docx', '📝', 'DOCX', 'Editing, annotating, and quoting')):
        name = f'{revision.book_name}.{ext}'
        if name in assets:
            page.append(f'| {icon} {link(f"**{label}**", name)} | {use} | {megabytes(assets[name]["size"])} |')

    if dataset:
        download = str(dataset['download']).rstrip('/')
        page += ['', '## 🗄️ The Charles River dataset', '',
                 f'Every chapter works with the Charles River Accounting Dataset. This edition is verified against '
                 f'release **{dataset["version"]}**, which covers {dataset.get("window", "its fiscal years")}. '
                 'Use these files, so that your results match the chapters: a later release can hold different '
                 'values.', '',
                 '| Format | Used for |', '|:--|:--|']
        for _key, label, file, use in DATASET_FILES:
            page.append(f'| [**{label}**]({download}/{file}) | {use} |')
        page += ['', f'The [dataset website]({DATASET_SITE}) has its documentation and every update'
                 + (f', and the [release page]({dataset["release"]}) lists the files.' if dataset.get('release')
                    else '.')]

    page += ['', '## 🎞️ Slides, companion files, and solutions', '',
             '**Slides** are the PowerPoint deck of each chapter or case. **Start files** hold the work as it stands at the end of the previous tutorial, so you can '
             'begin a tutorial without the one before it or check your own work. **Solutions** cover the exercises, '
             'the comprehensive cases, and the capstone cases, so try the work first. Every file explains itself, in '
             'a Solution Notes worksheet, a Power BI Notes page with a Checks query, or a SQL script\'s header and '
             'notes block.']
    if rows:
        page += ['', '| Chapter | Slides | Start files | Solutions |', '|:--|:--|:--|:--|']
        for row in rows:
            deck = f'{row.deck}.pptx'
            slides = link('PowerPoint', deck) if row.deck and deck in assets else '—'
            page.append(f'| {row.chapter} | {slides} | {links(row.companion)} | {links(row.solutions)} |')
    more = sorted((name for name, entry in assets.items() if entry.get('kind') in ('deck', 'companion')
                   and name not in used and name != INSTRUCTOR_NOTES))
    if more:
        page += ['', f'More files: ' + ' · '.join(link(name, name) for name in more) + '.']
    if INSTRUCTOR_NOTES in assets:
        page += ['', '## 👩‍🏫 For instructors', '',
                 f'{link(f"**{INSTRUCTOR_NOTES}**", INSTRUCTOR_NOTES)} collects the instructor notes, the expected '
                 'values of the tutorials, and the answer keys of the multiple-choice questions for every chapter, '
                 'case, and appendix, as Markdown and Word files.']
    page += ['', '## 🧭 Opening a companion file', '',
             'The Excel and Power BI files read CharlesRiver.xlsx from the folder `C:\\CharlesRiver`. If your copy '
             'is there, a file is ready to refresh; otherwise, point the file at your copy once before you refresh '
             f'it. The [Downloads page]({downloads}#sec-companion-files) explains each step for Excel and for Power '
             'BI Desktop.']

    published = str(manifest.get('updated') or '')[:10]
    page += ['', '## ℹ️ About this release', '',
             f'- **Revision:** {revision.revision} of the {revision.edition} edition (tag `{revision.tag}`).',
             f'- **Published** from commit [`{commit[:7]}`]({repo}/commit/{commit})'
             + (f' on {published}' if published else '') + '. `manifest.json` lists the size, the SHA-256, and the '
             'build commit of each file.',
             '- **License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/): share and adapt the '
             'book with attribution, under the same terms.',
             '', '<details>', '<summary><strong>Checksums</strong> (SHA-256)</summary>', '',
             '| File | SHA-256 |', '|:--|:--|']
    for key, _label, file, _use in DATASET_FILES if dataset else ():
        digest = (dataset.get('sha256') or {}).get(key)
        if digest:
            page.append(f'| `{file}` (dataset {dataset["version"]}) | `{digest}` |')
    # The book in the order of its formats, then the decks, then the companion files.
    order = [f'{revision.book_name}.{ext}' for ext in BOOK_FORMATS]
    kinds = ('deck', 'companion')
    for name, entry in sorted(assets.items(), key=lambda item: (
            order.index(item[0]) if item[0] in order else len(order),
            kinds.index(item[1]['kind']) if item[1].get('kind') in kinds else len(kinds), item[0])):
        if entry.get('sha256'):
            page.append(f'| `{name}` | `{entry["sha256"]}` |')
    page += ['', '</details>', '']
    return '\n'.join(page)


def stage(root: Path, assets: dict[str, Asset], names: list[str]) -> Path:
    """The files to upload under their release names (gh uploads a file under its own name)."""
    folder = root / STAGE
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    for name in names:
        try:
            os.link(assets[name].path, folder / name)
        except OSError:
            shutil.copy2(assets[name].path, folder / name)
    return folder


def publish(root: Path, *, build: bool = True, dry_run: bool = False, force: bool = False,
            github: GitHub | None = None) -> None:
    revision = read_revision(root)
    github = github or GitHub(revision.repo)
    github.authenticated()
    branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD')
    if branch != 'main':
        raise ValueError(f'Publish from main; this checkout is on {branch}.')
    dirty = git(root, 'status', '--porcelain', '--untracked-files=all')
    if dirty:
        raise ValueError('Commit your changes first: a revision is published from a commit.\n' + dirty[:2000])
    git(root, 'fetch', '--quiet', 'origin', 'main')
    remote_main, head = git(root, 'rev-parse', 'refs/remotes/origin/main'), git(root, 'rev-parse', 'HEAD')
    if subprocess.run(['git', 'merge-base', '--is-ancestor', remote_main, head], cwd=root, check=False).returncode:
        raise ValueError('origin/main has commits that this branch lacks: pull them first.')
    tree = head_tree(root)

    assets = expected_assets(root, revision)
    refresh(root, tree, assets, build=build)
    missing = [asset for asset in assets.values() if not asset.path.is_file()]
    if missing:
        raise ValueError('Missing local files (the companion files come from python scripts/companion/build.py '
                         '--publish):\n  ' + '\n  '.join(str(a.path.relative_to(root)) for a in missing))
    recorded = load_fingerprints(root)
    entries = {name: local_entry(asset, head, recorded) for name, asset in assets.items()}

    release = github.release(revision.tag)
    remote_names = {asset['name'] for asset in (release or {}).get('assets', [])}
    remote_manifest = github.manifest(revision.tag) if MANIFEST in remote_names else None
    uploads, deletes, kept = plan_uploads(entries, remote_names, remote_manifest, force)
    manifest = {'revision': revision.revision, 'tag': revision.tag, 'commit': head,
                'updated': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
                'assets': {name: kept.get(name, entries[name]) for name in sorted(entries)}}

    total = sum(entries[name]['size'] for name in uploads)
    print(f'Revision {revision.revision}: release {revision.tag} '
          f'{"exists" if release else "will be created (tag at " + head[:7] + ")"}.')
    print(f'Upload {len(uploads)} of {len(entries)} files ({megabytes(total)}); '
          f'{len(kept)} unchanged on the release.')
    for name in uploads:
        print(f'  upload  {name} ({megabytes(entries[name]["size"])})')
    for name in deletes:
        print(f'  delete  {name} (no longer linked by the book)')
    deploy = 'run the deploy workflow' if remote_main == head else f'push main ({remote_main[:7]}..{head[:7]})'
    print(f'Then {deploy}.', flush=True)
    text = release_notes(revision, head, manifest, rows=downloads_rows(root, revision), dataset=read_dataset(root))
    if dry_run:
        preview = root / STAGE / 'release-notes.md'
        preview.parent.mkdir(parents=True, exist_ok=True)
        preview.write_text(text, encoding='utf-8')
        print(f'The release page is previewed in {preview.relative_to(root)}.')
        print('Dry run: nothing was tagged, uploaded, or pushed.')
        return

    folder = stage(root, assets, uploads)
    notes = folder / 'release-notes.md'
    notes.write_text(text, encoding='utf-8')
    if release is None:
        if not git(root, 'ls-remote', '--tags', 'origin', f'refs/tags/{revision.tag}'):
            if subprocess.run(['git', 'rev-parse', '--verify', '--quiet', f'refs/tags/{revision.tag}'], cwd=root,
                              capture_output=True, check=False).returncode:
                git(root, 'tag', '-a', revision.tag, '-m', revision.title, 'HEAD')
            subprocess.run(['git', 'push', 'origin', f'refs/tags/{revision.tag}'], cwd=root, check=True)
        github.create(revision.tag, revision.title, notes)
    for number, name in enumerate(uploads, 1):
        print(f'[{number}/{len(uploads)}] {name} ({megabytes(entries[name]["size"])})', flush=True)
        github.upload(revision.tag, folder / name)
    for name in deletes:
        github.delete_asset(revision.tag, name)
    (folder / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    github.upload(revision.tag, folder / MANIFEST)
    github.edit_notes(revision.tag, notes)
    if remote_main == head:
        github.run_workflow(WORKFLOW, 'main')
        print('main was already pushed, so the deploy workflow was started.')
    else:
        subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/main'], cwd=root, check=True)
    print(f'Published the {revision.edition} edition, revision {revision.revision}: {revision.release}')
    print('GitHub Actions now renders and deploys the site.')


def notes(root: Path, *, update: bool = False, github: GitHub | None = None) -> Path:
    """Write the release page from the revision's published manifest to outputs/release/release-notes.md, and with
    update replace the text of the release with it (the files are not touched). publish does the same at its end."""
    revision = read_revision(root)
    github = github or GitHub(revision.repo)
    github.authenticated()
    if github.release(revision.tag) is None:
        raise ValueError(f'The release {revision.tag} does not exist yet: publish the revision first.')
    manifest = github.manifest(revision.tag)
    if manifest is None:
        raise ValueError(f'The release {revision.tag} has no {MANIFEST}: publish the revision first.')
    text = release_notes(revision, manifest.get('commit') or git(root, 'rev-parse', 'HEAD'), manifest,
                         rows=downloads_rows(root, revision), dataset=read_dataset(root))
    path = root / STAGE / 'release-notes.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    if update:
        github.edit_notes(revision.tag, path)
        print(f'Replaced the text of the release {revision.tag}: {revision.release}')
    else:
        print(f'Wrote {path.relative_to(root)}; add --update to put it on the release.')
    return path


# --- Status and the check on GitHub Actions -------------------------------------------------------------------------

def status(root: Path, github: GitHub | None = None) -> None:
    revision = read_revision(root)
    tree = working_tree(root)
    assets = expected_assets(root, revision)
    recorded = load_fingerprints(root)
    release = manifest = None
    try:
        github = github or GitHub(revision.repo)
        release = github.release(revision.tag)
        names = {asset['name'] for asset in (release or {}).get('assets', [])}
        manifest = github.manifest(revision.tag) if MANIFEST in names else None
    except RuntimeError as exc:
        names = set()
        print(f'(The release cannot be read: {exc})')
    print(f'{revision.title}, release {revision.tag}: '
          f'{"published" if release else "not created yet"} ({revision.release})')
    remote = (manifest or {}).get('assets') or {}
    print(f'{"file":<42} {"local":<8} {"build":<8} release')
    for name, asset in assets.items():
        local = 'present' if asset.path.is_file() else 'missing'
        current = fingerprint(root, tree, inputs_of(root, tree, asset.deck)) if asset.kind in BUILT else None
        built = recorded['book'] if asset.kind == 'book' else recorded['decks'].get(asset.deck)
        build = '-' if current is None else ('current' if built == current else 'stale')
        if name not in names:
            state = 'missing'
        elif asset.kind in BUILT:
            state = 'current' if (remote.get(name) or {}).get('inputs') == current else 'older'
        else:
            state = ('same' if asset.path.is_file() and (remote.get(name) or {}).get('sha256') == sha256(asset.path)
                     else 'different')
        print(f'{name:<42} {local:<8} {build:<8} {state}')
    for name in sorted(names - set(assets) - {MANIFEST}):
        print(f'{name:<42} {"-":<8} {"-":<8} on the release, no longer linked')


def report(errors: list[str], warnings: list[str], summary: Path | None) -> None:
    actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    for kind, messages in (('error', errors), ('warning', warnings)):
        for message in messages:
            print(f'::{kind}::{message}' if actions else f'{kind.upper()}: {message}', flush=True)
    if summary:
        lines = ['## Release files', '']
        lines += [f'- :x: {m}' for m in errors] + [f'- :warning: {m}' for m in warnings]
        if not errors and not warnings:
            lines.append('- Every file the site links is on the release and was built from the current text.')
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write('\n'.join(lines) + '\n')


def check(root: Path, site: Path, github: GitHub | None = None, summary: Path | None = None) -> int:
    """Fail when the site links a file the release lacks; warn when a book or deck file predates the text."""
    revision = read_revision(root)
    errors, warnings = [], []
    linked = site_links(site, revision)
    if not linked:
        errors.append(f'The site in {site} links no release files: did filters/slide-links.lua run?')
    github = github or GitHub(revision.repo)
    release = github.release(revision.tag)
    if release is None:
        errors.append(f'The release {revision.tag} does not exist yet: publish the revision with '
                      'python scripts/release.py publish.')
    else:
        names = {asset['name'] for asset in release.get('assets', [])}
        for name in sorted(linked - names):
            errors.append(f'The site links {name}, which the release {revision.tag} lacks: '
                          'publish it with python scripts/release.py publish.')
        manifest = github.manifest(revision.tag) if MANIFEST in names else None
        if manifest is None:
            warnings.append(f'The release {revision.tag} has no {MANIFEST}, so its files cannot be compared with '
                            'the text.')
        else:
            tree = head_tree(root)
            for name, entry in sorted((manifest.get('assets') or {}).items()):
                if entry.get('kind') not in BUILT or name not in linked:
                    continue
                changed = changed_inputs(entry.get('inputs') or {},
                                         fingerprint(root, tree, inputs_of(root, tree, entry.get('deck'))))
                if changed:
                    shown = ', '.join(changed[:6]) + (', ...' if len(changed) > 6 else '')
                    warnings.append(f'{name} on the release was built before changes to {shown}; refresh it with '
                                    'python scripts/release.py publish.')
    report(errors, warnings, summary)
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status', help='what is built, current, and on the release')
    publishing = commands.add_parser('publish', help='build what is stale, upload what changed, push main')
    publishing.add_argument('--no-build', action='store_true', help='refuse instead of building stale files')
    publishing.add_argument('--dry-run', action='store_true', help='show the plan; tag, upload and push nothing')
    publishing.add_argument('--force', action='store_true', help='upload every file, changed or not')
    describing = commands.add_parser('notes', help='write the release page (--update puts it on the release)')
    describing.add_argument('--update', action='store_true', help='replace the text of the release with it')
    bumping = commands.add_parser('bump', help='start a new revision in _variables.yml')
    bumping.add_argument('revision', help='for example 2027.2')
    checking = commands.add_parser('check', help='GitHub Actions: the release holds every file the site links')
    checking.add_argument('--site', type=Path, default=ROOT / '_book')
    args = parser.parse_args(argv)
    try:
        if args.command == 'status':
            status(ROOT)
        elif args.command == 'publish':
            publish(ROOT, build=not args.no_build, dry_run=args.dry_run, force=args.force)
        elif args.command == 'notes':
            notes(ROOT, update=args.update)
        elif args.command == 'bump':
            revision = bump(ROOT, args.revision)
            print(f'_variables.yml now names revision {revision.revision} ({revision.tag}). Commit it, then run '
                  'python scripts/release.py publish, which creates the release.')
        else:
            summary = os.environ.get('GITHUB_STEP_SUMMARY')
            return check(ROOT, args.site, summary=Path(summary) if summary else None)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
