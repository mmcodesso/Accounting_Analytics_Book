"""Release bundles use an allowlist; live checks compare notes and resources."""
import json
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import zipfile

from scripts.slides import package_release as package
from scripts.slides import verify_published as published
from scripts.slides.verify import sha256


def write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode('utf-8'))
    return path


def manifest():
    return {'book_url': 'https://example.invalid/book/', 'chapters': [
        {'id': 'chapter-01', 'status': 'approved', 'source': 'chapter-01/index.qmd',
         'book_sources': ['chapters/01-role-of-analytics/chapter.qmd']}]}


def powerpoint(*, notes='Public narration', modified='first render'):
    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('ppt/slides/slide1.xml', '<slide>Native teaching text</slide>')
        archive.writestr('ppt/notesSlides/notesSlide1.xml', notes)
        archive.writestr('ppt/media/figure.png', b'figure data')
        archive.writestr('docProps/core.xml', modified)
    return stream.getvalue()


class PackageTests(unittest.TestCase):
    def fixture(self, root):
        write(root, 'slides/manifest.yml', json.dumps(manifest()))
        write(root, 'outputs/build/build-report.json', json.dumps({
            'mode': 'book-and-slides', 'automated_artifact_checks': 'passed', 'includes_pilot': False}))
        write(root, '_book/slides/chapter-01/index.html', '<html/>')
        write(root, '_book/slides/chapter-01/chapter-01.pptx', powerpoint())
        write(root, '_book/slides/chapter-01/runtime/speaker-view.html', '<html>Speaker view</html>')
        files = []
        for relative, content in [('slides/manifest.yml', json.dumps(manifest())),
                                  ('slides/chapter-01/index.qmd', '## Teaching slide\nPublic notes')]:
            path = write(root, 'outputs/public-export/' + relative, content)
            files.append({'path': relative, 'sha256': sha256(path)})
        report = {'review_only': False, 'validation': {'source_audit': 'passed'},
                  'chapter_ids': ['chapter-01'], 'files': files}
        write(root, 'outputs/public-export/export-manifest.json', json.dumps(report))
        write(root, 'outputs/public-export/TRANSFER.md', 'Manual transfer instructions')
        return report

    def test_packages_rebuild_from_current_products_and_exclude_unlisted_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            write(root, 'outputs/public-export/facts/not-for-release.txt', 'Outside the approved inventory')
            with patch.object(package, 'source_checks', return_value=[]), \
                 patch.object(package, 'verify_outputs', return_value=[]):
                packages = package.package_release(root)
            self.assertEqual(2, len(packages))
            with zipfile.ZipFile(root / 'outputs/chapter-slides.zip') as archive:
                self.assertIn('slides/chapter-01/runtime/speaker-view.html', archive.namelist())
            with zipfile.ZipFile(root / 'outputs/chapter-slides-public-source.zip') as archive:
                self.assertIn('slides/chapter-01/index.qmd', archive.namelist())
                self.assertNotIn('facts/not-for-release.txt', archive.namelist())
            self.assertTrue((root / 'outputs/build/release-packages.json').is_file())

    def test_changed_export_is_rejected_before_previous_bundle_is_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            prior = write(root, 'outputs/chapter-slides.zip', b'previous reviewed bundle')
            write(root, 'outputs/public-export/slides/chapter-01/index.qmd', 'Unreviewed change')
            with patch.object(package, 'source_checks', return_value=[]), \
                 patch.object(package, 'verify_outputs', return_value=[]), \
                 self.assertRaisesRegex(ValueError, 'Public bundle input changed'):
                package.package_release(root)
            self.assertEqual(b'previous reviewed bundle', prior.read_bytes())

    def test_protected_path_cannot_be_added_to_export_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.fixture(root)
            path = write(root, 'outputs/public-export/facts/not-for-release.txt', 'Outside the approved inventory')
            report['files'].append({'path': 'facts/not-for-release.txt', 'sha256': sha256(path)})
            write(root, 'outputs/public-export/export-manifest.json', json.dumps(report))
            with patch.object(package, 'source_checks', return_value=[]), \
                 patch.object(package, 'verify_outputs', return_value=[]), \
                 self.assertRaisesRegex(ValueError, 'Private path'):
                package.package_release(root)


class PublishedChecksTests(unittest.TestCase):
    def fixture(self, root, *, notes='Public narration'):
        write(root, 'slides/manifest.yml', json.dumps(manifest()))
        document = b'<html><script src="runtime.js"></script><link href="theme.css" rel="stylesheet"></html>'
        write(root, 'slides/_build/revealjs/chapter-01/index.html', document)
        write(root, 'slides/_build/pptx/chapter-01/chapter-01.pptx', powerpoint())
        base = '/book/slides/chapter-01/'
        remote = {base + 'index.html': document, base + 'runtime.js': b'local runtime',
                  base + 'theme.css': b'@font-face {src: url("fonts/Arial.woff2");}',
                  base + 'fonts/Arial.woff2': b'font data',
                  base + 'index_files/libs/revealjs/plugin/notes/speaker-view.html': b'speaker view',
                  base + 'chapter-01.pptx': powerpoint(notes=notes, modified='later render'),
                  '/book/chapters/01-role-of-analytics/chapter.html':
                      b'<a href="/book/slides/chapter-01/index.html">View</a>'
                      b'<a href="/book/slides/chapter-01/chapter-01.pptx">Download</a>'}
        return remote

    def test_live_check_includes_css_resources_and_ignores_pptx_render_timestamps(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            remote = self.fixture(root)
            with patch.object(published, 'source_checks', return_value=[]), \
                 patch.object(published, 'verify_outputs', return_value=[]), \
                 patch.object(published, 'fetch', side_effect=lambda url: remote[urlsplit(url).path]):
                report = published.verify_published(root, 'chapter-01', release='test')
            self.assertEqual(4, report['local_resources_checked'])
            self.assertEqual('passed', report['speaker_view_resource'])
            self.assertTrue((root / 'outputs/build/chapter-01/live-site-verification.json').is_file())

    def test_revised_public_notes_require_new_published_pptx(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            remote = self.fixture(root, notes='Outdated narration')
            with patch.object(published, 'source_checks', return_value=[]), \
                 patch.object(published, 'verify_outputs', return_value=[]), \
                 patch.object(published, 'fetch', side_effect=lambda url: remote[urlsplit(url).path]), \
                 self.assertRaisesRegex(ValueError, 'PowerPoint slides, notes, or images differ'):
                published.verify_published(root, 'chapter-01', release='test')
            self.assertFalse((root / 'outputs/build/chapter-01/live-site-verification.json').exists())


if __name__ == '__main__':
    unittest.main()
