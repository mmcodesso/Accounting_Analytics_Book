#!/usr/bin/env python3
"""Publish a revision of the book as a GitHub release, and check that release from GitHub Actions.

GitHub Actions renders the site: the book's HTML and the Reveal decks. The files the site links but does not serve
are built locally and published as the assets of the revision's release (the book block of _variables.yml): the PDF,
EPUB and DOCX, a PowerPoint file per deck, and the companion and solution files. filters/slide-links.lua points the
links at the release. A new revision is a new tag and release; publishing the same revision again uploads only the
files that changed.

  python scripts/release.py status                    what is built, current, and on the release
  python scripts/release.py publish [--dry-run]       build what is stale, upload what changed, push main
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
    """The input paths of the book's PDF, EPUB and DOCX, or of one deck (with its own chapter's folder)."""
    if deck is None:
        return list(BOOK_INPUTS)
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
    if after != tree:
        print('WARNING: the sources changed during the build, so its files are not recorded as current; '
              'build again before publishing.', flush=True)
        return
    data = load_fingerprints(root)
    if book:
        data['book'] = fingerprint(root, tree, inputs_of(root, tree))
    for deck in decks:
        data['decks'][deck] = fingerprint(root, tree, inputs_of(root, tree, deck))
    path = root / FINGERPRINTS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


# --- The files of a revision ----------------------------------------------------------------------------------------

class Asset:
    def __init__(self, name: str, kind: str, path: Path, deck: str | None = None):
        self.name, self.kind, self.path, self.deck = name, kind, path, deck


def deck_ids(root: Path) -> list[str]:
    return sorted(path.parent.name for path in (root / 'slides').glob('chapter-[0-9][0-9]/index.qmd'))


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
    commands = ([[sys.executable, 'scripts/build_all.py']] if book else
                [[sys.executable, 'scripts/build_all.py', '--slides-only', '--chapter', deck] for deck in decks])
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


def release_notes(revision: Revision, commit: str, manifest: dict) -> str:
    assets = manifest['assets']
    decks = sorted(name for name, entry in assets.items() if entry['kind'] == 'deck')
    companion = sum(1 for entry in assets.values() if entry['kind'] == 'companion')
    return '\n'.join([
        f'Revision {revision.revision} of the {revision.edition} edition of *Accounting Analytics: An Integrated '
        'Approach*.',
        '',
        f'- The book: {", ".join(f"`{revision.book_name}.{ext}`" for ext in BOOK_FORMATS)}.',
        f'- The slides: {len(decks)} PowerPoint decks (`chapter-NN.pptx`).',
        f'- The companion and solution files: {companion} files, listed on the book\'s Downloads page.',
        '',
        f'Last published from commit {commit[:7]} on {dt.date.today().isoformat()}. `manifest.json` lists each '
        'file\'s size, SHA-256, and the commit it was built from.',
        ''])


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
    manifest = {'revision': revision.revision, 'tag': revision.tag,
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
    if dry_run:
        print('Dry run: nothing was tagged, uploaded, or pushed.')
        return

    folder = stage(root, assets, uploads)
    notes = folder / 'release-notes.md'
    notes.write_text(release_notes(revision, head, manifest), encoding='utf-8')
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
