"""The release of a revision (scripts/release.py): the book block of _variables.yml, the files a revision holds, the
fingerprints that say whether a built file is current, the upload plan, and the check GitHub Actions runs. A fake
stands in for the GitHub CLI; the fingerprint tests build a small git repository and are skipped without git."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import release

HAS_GIT = shutil.which('git') is not None
REPO = 'https://github.com/owner/book'
VARIABLES = f'''# Values the book reads.
book:
  # The edition and the revision.
  edition: "first"
  revision: "2001.1"
  tag: "book-v2001.1"
  release: "{REPO}/releases/tag/book-v2001.1"
  download: "{REPO}/releases/download/book-v2001.1"

dataset:
  version: "v2000.1"
'''
DOWNLOAD = f'{REPO}/releases/download/book-v2001.1'


def write(root: Path, rel: str, text: str = 'fixture') -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def book(root: Path) -> None:
    """A tiny book: one chapter with a deck, the Downloads page's links, and the built files."""
    write(root, '_variables.yml', VARIABLES)
    write(root, 'index.qmd', '# Home\n')
    write(root, 'chapters/01-intro/chapter.qmd', '# Intro\n')
    write(root, 'chapters/02-next/chapter.qmd', '# Next\n')
    write(root, 'slides/chapter-01/index.qmd', '## Slide\n')
    write(root, 'front-matter/downloads.qmd', '\n'.join([
        '- [PDF](/downloads/book-latest.pdf)', '- [EPUB](/downloads/book-latest.epub)',
        '- [DOCX](/downloads/book-latest.docx)',
        '| [Start files](/supplementary/start-files/Chapter01-companion.zip) |',
        '| [Excel](/supplementary/solutions/Chapter01-exercises.zip) |', '']))
    for ext in release.BOOK_FORMATS:
        write(root, f'{release.DOWNLOADS}/book-latest.{ext}', ext)
    write(root, f'{release.PPTX}/chapter-01/chapter-01.pptx', 'deck')
    write(root, 'supplementary/start-files/Chapter01-companion.zip', 'start')
    write(root, 'supplementary/solutions/Chapter01-exercises.zip', 'solution')


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                           '-c', 'commit.gpgsign=false', *args],
                          cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def commit_all(root: Path) -> None:
    if not (root / '.git').exists():
        git(root, 'init', '-q')
        write(root, '.gitignore', 'outputs/\nsupplementary/*\n')
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', 'state')


class FakeGitHub:
    def __init__(self, names=None, manifest=None, exists=True):
        self.names, self.data, self.exists = list(names or []), manifest, exists

    def release(self, tag):
        return {'assets': [{'name': name} for name in self.names]} if self.exists else None

    def manifest(self, tag):
        return self.data


class RevisionTests(unittest.TestCase):
    def test_the_book_block_names_the_release_and_its_download_address(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, '_variables.yml', VARIABLES)
            revision = release.read_revision(root)
            self.assertEqual(('2001.1', 'book-v2001.1', 'owner/book'), (revision.revision, revision.tag, revision.repo))
            self.assertEqual(f'{DOWNLOAD}/Accounting_Analytics_First_Edition_Rev_2001_1.pdf', revision.url('Accounting_Analytics_First_Edition_Rev_2001_1.pdf'))
            self.assertEqual('First edition, revision 2001.1', revision.title)

    def test_the_book_files_are_named_from_the_edition_and_the_revision(self) -> None:
        def name(edition, number):
            tag = f'book-v{number}'
            return release.Revision(number, tag, f'{REPO}/releases/tag/{tag}', f'{REPO}/releases/download/{tag}',
                                    edition).book_name
        self.assertEqual('Accounting_Analytics_First_Edition_Rev_2027_1', name('first', '2027.1'))
        self.assertEqual('Accounting_Analytics_Second_Edition_Rev_2028_12', name('second', '2028.12'))
        self.assertEqual('Accounting_Analytics_First_Revised_Edition_Rev_2027_2', name('first revised', '2027.2'))

    def test_a_url_of_another_tag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, '_variables.yml', VARIABLES.replace('download/book-v2001.1', 'download/book-v2000.9'))
            with self.assertRaisesRegex(ValueError, 'book.download'):
                release.read_revision(root)

    def test_bump_rewrites_only_the_book_block_and_keeps_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / '_variables.yml'
            path.write_bytes(VARIABLES.replace('\n', '\r\n').encode('utf-8'))
            revision = release.bump(root, '2001.2')
            self.assertEqual(('2001.2', 'book-v2001.2'), (revision.revision, revision.tag))
            text = path.read_bytes().decode('utf-8')
            self.assertEqual(text.count('\n'), text.count('\r\n'))
            self.assertIn('  # The edition and the revision.', text)
            self.assertIn('edition: "first"', text)
            self.assertIn('version: "v2000.1"', text)
            self.assertIn(f'download: "{REPO}/releases/download/book-v2001.2"', text)
            self.assertIn('Accounting_Analytics_First_Edition_Rev_2001_2.pdf', release.expected_assets(root))
            with self.assertRaisesRegex(ValueError, 'year and a number'):
                release.bump(root, 'next')


class AssetTests(unittest.TestCase):
    def test_the_revision_holds_the_book_each_deck_and_each_linked_companion_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book(root)
            assets = release.expected_assets(root)
            self.assertEqual({'Accounting_Analytics_First_Edition_Rev_2001_1.pdf', 'Accounting_Analytics_First_Edition_Rev_2001_1.epub', 'Accounting_Analytics_First_Edition_Rev_2001_1.docx',
                              'chapter-01.pptx', 'Chapter01-companion.zip', 'Chapter01-exercises.zip'}, set(assets))
            self.assertEqual(root / 'supplementary/solutions/Chapter01-exercises.zip',
                             assets['Chapter01-exercises.zip'].path)
            self.assertEqual('chapter-01', assets['chapter-01.pptx'].deck)

    def test_two_files_with_one_release_name_and_unknown_downloads_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book(root)
            write(root, 'cases/case.qmd', '[x](/supplementary/other/Chapter01-exercises.zip)\n')
            with self.assertRaisesRegex(ValueError, 'same name'):
                release.expected_assets(root)
            write(root, 'cases/case.qmd', '[x](/downloads/notes.txt)\n')
            with self.assertRaisesRegex(ValueError, 'not a release file'):
                release.expected_assets(root)

    def test_the_site_links_are_read_from_every_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, '_variables.yml', VARIABLES)
            write(root, '_book/front-matter/downloads.html',
                  f'<a href="{DOWNLOAD}/Accounting_Analytics_First_Edition_Rev_2001_1.pdf">PDF</a> <a href="/slides/x.html">x</a>')
            write(root, '_book/chapters/01/chapter.html', f'<a href="{DOWNLOAD}/Notes%20A&amp;B.zip">N</a>')
            names = release.site_links(root / '_book', release.read_revision(root))
            self.assertEqual({'Accounting_Analytics_First_Edition_Rev_2001_1.pdf', 'Notes A&B.zip'}, names)


class PlanTests(unittest.TestCase):
    ENTRIES = {
        'Accounting_Analytics_First_Edition_Rev_2001_1.pdf': {'kind': 'book', 'sha256': 'new-bytes', 'inputs': {'chapters': 'a'}},
        'chapter-01.pptx': {'kind': 'deck', 'deck': 'chapter-01', 'sha256': 'x', 'inputs': {'slides/chapter-01': 'b2'}},
        'Chapter01-companion.zip': {'kind': 'companion', 'sha256': 'same'},
        'Chapter01-exercises.zip': {'kind': 'companion', 'sha256': 'changed'},
        'chapter-02.pptx': {'kind': 'deck', 'deck': 'chapter-02', 'sha256': 'y', 'inputs': {'slides/chapter-02': 'c'}},
    }
    REMOTE = {'assets': {
        'Accounting_Analytics_First_Edition_Rev_2001_1.pdf': {'kind': 'book', 'sha256': 'old-bytes', 'inputs': {'chapters': 'a'}},
        'chapter-01.pptx': {'kind': 'deck', 'deck': 'chapter-01', 'sha256': 'x', 'inputs': {'slides/chapter-01': 'b1'}},
        'Chapter01-companion.zip': {'kind': 'companion', 'sha256': 'same'},
        'Chapter01-exercises.zip': {'kind': 'companion', 'sha256': 'before'},
    }}
    NAMES = {'Accounting_Analytics_First_Edition_Rev_2001_1.pdf', 'chapter-01.pptx', 'Chapter01-companion.zip', 'Chapter01-exercises.zip',
             'Retired.zip', 'manifest.json'}

    def test_only_what_changed_is_uploaded(self) -> None:
        uploads, deletes, kept = release.plan_uploads(self.ENTRIES, self.NAMES, self.REMOTE)
        # The PDF was rebuilt from the same inputs (new bytes, same content): the release keeps its copy.
        self.assertEqual(['chapter-01.pptx', 'Chapter01-exercises.zip', 'chapter-02.pptx'], uploads)
        self.assertEqual({'Accounting_Analytics_First_Edition_Rev_2001_1.pdf', 'Chapter01-companion.zip'}, set(kept))
        self.assertEqual('old-bytes', kept['Accounting_Analytics_First_Edition_Rev_2001_1.pdf']['sha256'])
        self.assertEqual(['Retired.zip'], deletes)

    def test_force_and_a_release_without_a_manifest_upload_everything(self) -> None:
        self.assertEqual(len(self.ENTRIES), len(release.plan_uploads(self.ENTRIES, self.NAMES, self.REMOTE, True)[0]))
        self.assertEqual(len(self.ENTRIES), len(release.plan_uploads(self.ENTRIES, self.NAMES, None)[0]))


@unittest.skipUnless(HAS_GIT, 'git is not installed')
class FingerprintTests(unittest.TestCase):
    def test_a_build_is_current_until_one_of_its_inputs_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book(root)
            commit_all(root)
            tree = release.working_tree(root)
            self.assertEqual(release.head_tree(root), tree)
            assets = release.expected_assets(root)
            self.assertEqual((True, ['chapter-01']), release.stale_builds(root, tree, assets))
            release.record_build(root, tree, book=True, decks=['chapter-01'])
            self.assertEqual((False, []), release.stale_builds(root, tree, assets))

            # Another chapter's text dates the book but not chapter 1's deck.
            write(root, 'chapters/02-next/chapter.qmd', '# Next, revised\n')
            commit_all(root)
            tree = release.head_tree(root)
            self.assertEqual((True, []), release.stale_builds(root, tree, assets))
            # Chapter 1's own text dates its deck too.
            write(root, 'chapters/01-intro/chapter.qmd', '# Intro, revised\n')
            commit_all(root)
            tree = release.head_tree(root)
            self.assertEqual((True, ['chapter-01']), release.stale_builds(root, tree, assets))
            recorded = release.load_fingerprints(root)['decks']['chapter-01']
            current = release.fingerprint(root, tree, release.inputs_of(root, tree, 'chapter-01'))
            self.assertEqual(['chapters/01-intro'], release.changed_inputs(recorded, current))

    def test_a_build_whose_sources_changed_meanwhile_is_not_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book(root)
            commit_all(root)
            tree = release.working_tree(root)
            write(root, 'chapters/01-intro/chapter.qmd', '# Edited during the build\n')
            release.record_build(root, tree, book=True, decks=['chapter-01'])
            self.assertFalse((root / release.FINGERPRINTS).exists())

    def test_the_check_fails_on_a_missing_file_and_only_warns_on_a_stale_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book(root)
            commit_all(root)
            tree = release.head_tree(root)
            write(root, '_book/front-matter/downloads.html', ''.join(
                f'<a href="{DOWNLOAD}/{name}">x</a>' for name in ('Accounting_Analytics_First_Edition_Rev_2001_1.pdf', 'chapter-01.pptx')))
            built = {'kind': 'deck', 'deck': 'chapter-01',
                     'inputs': release.fingerprint(root, tree, release.inputs_of(root, tree, 'chapter-01'))}
            manifest = {'assets': {'chapter-01.pptx': built, 'Accounting_Analytics_First_Edition_Rev_2001_1.pdf': {
                'kind': 'book', 'inputs': release.fingerprint(root, tree, release.inputs_of(root, tree))}}}
            names = ['Accounting_Analytics_First_Edition_Rev_2001_1.pdf', 'chapter-01.pptx', 'manifest.json']
            summary = root / 'summary.md'
            self.assertEqual(0, release.check(root, root / '_book', FakeGitHub(names, manifest), summary))
            self.assertIn('Every file the site links is on the release', summary.read_text(encoding='utf-8'))

            write(root, 'slides/chapter-01/index.qmd', '## Slide, revised\n')
            commit_all(root)
            self.assertEqual(0, release.check(root, root / '_book', FakeGitHub(names, manifest), summary))
            self.assertIn('chapter-01.pptx on the release was built before changes to slides/chapter-01',
                          summary.read_text(encoding='utf-8'))

            self.assertEqual(1, release.check(root, root / '_book', FakeGitHub(names[1:], manifest), None))
            self.assertEqual(1, release.check(root, root / '_book', FakeGitHub(exists=False), None))


if __name__ == '__main__':
    unittest.main()
