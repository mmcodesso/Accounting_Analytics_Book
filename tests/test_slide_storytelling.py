"""Scoped builds preserve other decks; provenance checks require no dataset."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_all
from scripts.slides import refresh_storytelling as story
from scripts.slides.verify import load_manifest


ROOT = Path(__file__).resolve().parents[1]


class FocusedBuildTests(unittest.TestCase):
    def test_selection_excludes_unrelated_editorial_staleness(self):
        manifest = load_manifest(ROOT / 'slides/manifest.yml')
        manifest['chapters'][17]['reviewed_source_hashes'][manifest['chapters'][17]['book_sources'][0]] = 'changed'
        self.assertEqual([], build_all.source_checks(ROOT, manifest, 'chapter-01'))
        self.assertTrue(any('chapter-18: editorial review required' in error
                            for error in build_all.source_checks(ROOT, manifest)))

    def test_destructive_renderer_is_isolated_and_other_outputs_survive(self):
        manifest = {'toolchain': {'quarto': '1.9.36'}, 'chapters': [
            {'id': 'chapter-01', 'source': 'chapter-01/index.qmd', 'status': 'pilot'},
            {'id': 'chapter-02', 'source': 'chapter-02/index.qmd', 'status': 'approved'}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for fmt in ('revealjs', 'pptx'):
                other = root / 'slides/_build' / fmt / 'chapter-02/keep.txt'
                other.parent.mkdir(parents=True); other.write_text('approved')
            def fake_render(workdir, command, env):
                self.assertEqual('slides/chapter-01/index.qmd', command[2])
                relative = command[command.index('--output-dir') + 1]
                self.assertTrue(relative.startswith('_build/focused/chapter-01/'))
                target = root / 'slides' / relative / 'chapter-01/index.html'
                target.parent.mkdir(parents=True); target.write_text('revised')
            with patch.object(build_all, 'source_checks', return_value=[]), \
                 patch.object(build_all, 'prepare'), \
                 patch.object(build_all.subprocess, 'check_output', return_value='1.9.36'), \
                 patch.object(build_all, 'run', side_effect=fake_render), \
                 patch.object(build_all, 'verify_outputs', return_value=[]):
                build_all.build(root, manifest, 'quarto', slides_only=True, chapter_id='chapter-01')
            for fmt in ('revealjs', 'pptx'):
                self.assertEqual('approved', (root/'slides/_build'/fmt/'chapter-02/keep.txt').read_text())
                self.assertEqual('revised', (root/'slides/_build'/fmt/'chapter-01/index.html').read_text())
            report = json.loads((root/'outputs/build/chapter-01/build-report.json').read_text())
            self.assertEqual(['chapter-01'], report['chapters'])
            self.assertFalse((root/'outputs/build/build-report.json').exists())

    def test_selection_rejected_for_full_assembly_and_export(self):
        with self.assertRaisesRegex(ValueError, '--slides-only'):
            build_all.build(ROOT, {}, 'quarto', chapter_id='chapter-01')
        with patch('sys.argv', ['build_all.py', '--chapter', 'chapter-01', '--export-public']):
            self.assertEqual(1, build_all.main())

    def test_committed_storytelling_provenance_detects_modified_artifact(self):
        manifest = {'public_assets': [(story.OUTPUT/'facts.json').as_posix()]}
        self.assertEqual([], story.check_fresh(ROOT, manifest))
        original = story._content_hash
        def changed(path):
            return 'changed' if path.name == 'checked-credit.svg' else original(path)
        with patch.object(story, '_content_hash', side_effect=changed):
            self.assertTrue(any('checked-credit.svg' in error for error in story.check_fresh(ROOT, manifest)))


if __name__ == '__main__':
    unittest.main()
