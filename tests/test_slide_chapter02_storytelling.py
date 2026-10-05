"""Chapter 2 refresh isolation, dataset-free provenance, and pilot boundaries."""
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_all
from scripts.slides import refresh_chapter02_storytelling as story
from scripts.slides.verify import load_manifest

ROOT = Path(__file__).resolve().parents[1]


class Chapter02StorytellingTests(unittest.TestCase):
    def test_provenance_needs_no_dataset_and_detects_changed_inputs(self):
        manifest = {'public_assets': [(story.OUTPUT/'facts.json').as_posix()]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            names = set(story.GENERATORS+story.INPUTS+('_variables.yml',))
            names.update((story.OUTPUT/name).as_posix() for name in story.ASSETS+('facts.json',))
            for name in names:
                target = root/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/name,target)
            self.assertFalse((root/'datasets').exists())
            for newline in ('\n','\r\n'):
                for name in story.INPUTS:
                    path = root/name
                    path.write_bytes(path.read_text(encoding='utf-8').replace('\n',newline).encode('utf-8'))
                self.assertEqual([],story.check_fresh(root,manifest))
            diagram = root/story.INPUTS[-1]
            diagram.write_bytes(diagram.read_bytes()+b'changed')
            self.assertTrue(any('input_sha256 changed' in e for e in story.check_fresh(root,manifest)))

    def test_artifact_tampering_and_dataset_pin_changes_fail(self):
        manifest = {'public_assets': [(story.OUTPUT/'facts.json').as_posix()]}
        self.assertEqual([],story.check_fresh(ROOT,manifest))
        original = story.content_hash
        with patch.object(story,'content_hash',side_effect=lambda path:
                          'changed' if path.name=='_amount-task.qmd' else original(path)):
            self.assertTrue(any('_amount-task.qmd' in e for e in story.check_fresh(ROOT,manifest)))
        with patch.object(story,'_pin',return_value={'sha256':'changed'}):
            self.assertTrue(any('dataset pin changed' in e for e in story.check_fresh(ROOT,manifest)))

    def test_chapter02_refresh_does_not_refresh_chapter01_or_foundations(self):
        with patch('sys.argv',['build_all.py','--check','--chapter','chapter-02','--refresh-shared']), \
             patch.object(build_all,'source_checks',return_value=[]), \
             patch.object(story,'refresh') as refresh, \
             patch('scripts.slides.refresh.refresh') as chapter01, \
             patch('scripts.slides.refresh_foundations.refresh') as foundations:
            self.assertEqual(0,build_all.main())
        refresh.assert_called_once_with(ROOT)
        chapter01.assert_not_called()
        foundations.assert_not_called()

    def test_unrelated_staleness_is_excluded_only_from_focused_checks(self):
        manifest = load_manifest(ROOT/'slides/manifest.yml')
        chapter18 = next(c for c in manifest['chapters'] if c['id']=='chapter-18')
        chapter18['reviewed_source_hashes'][chapter18['book_sources'][0]] = 'changed'
        self.assertEqual([],build_all.source_checks(ROOT,manifest,'chapter-02'))
        self.assertTrue(any('chapter-18: editorial review required' in e
                            for e in build_all.source_checks(ROOT,manifest)))

    def test_focused_render_preserves_other_chapters(self):
        manifest = {'toolchain':{'quarto':'1.9.36'},'chapters':[
            {'id':'chapter-01','source':'chapter-01/index.qmd','status':'approved'},
            {'id':'chapter-02','source':'chapter-02/index.qmd','status':'pilot'}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for fmt in ('revealjs','pptx'):
                keep = root/'slides/_build'/fmt/'chapter-01/keep.txt'
                keep.parent.mkdir(parents=True); keep.write_text('approved')
            def renderer(workdir,command,env):
                self.assertEqual('slides/chapter-02/index.qmd',command[2])
                relative = command[command.index('--output-dir')+1]
                self.assertTrue(relative.startswith('_build/focused/chapter-02/'))
                product = root/'slides'/relative/'chapter-02/result.txt'
                product.parent.mkdir(parents=True); product.write_text('revised')
            with patch.object(build_all,'source_checks',return_value=[]), \
                 patch.object(build_all,'prepare'), \
                 patch.object(build_all.subprocess,'check_output',return_value='1.9.36'), \
                 patch.object(build_all,'run',side_effect=renderer), \
                 patch.object(build_all,'verify_outputs',return_value=[]):
                build_all.build(root,manifest,'quarto',slides_only=True,chapter_id='chapter-02')
            for fmt in ('revealjs','pptx'):
                self.assertEqual('approved',(root/'slides/_build'/fmt/'chapter-01/keep.txt').read_text())
            report = json.loads((root/'outputs/build/chapter-02/build-report.json').read_text())
            self.assertEqual(['chapter-02'],report['chapters'])

    def test_pilot_has_complete_notes_and_separate_prompt_responses(self):
        text = (ROOT/'slides/chapter-02/index.qmd').read_text(encoding='utf-8')
        self.assertEqual(4,len(re.findall(r'(?m)^# ',text)))
        self.assertEqual(45,len(re.findall(r'(?m)^## ',text)))
        self.assertNotIn('#ch02-summary',text)
        for section in re.split(r'(?m)^## ',text)[1:]:
            section = re.split(r'(?m)^# ',section)[0]
            for label in ('Purpose:','Evidence:','Timing:','Narration:','Expected response:','Misconception:','Transition:'):
                self.assertIn(label,section)
        for prompt,response in [('sources','source-response'),('date-task','date-response'),
                                ('balance-limit','balance-response'),('account-keys','account-response'),
                                ('amount-task','amount-response'),('checkpoint','model-assessment')]:
            self.assertLess(text.index('#ch02-'+prompt+' '),text.index('#ch02-'+response+' '))
        self.assertNotIn('**Check**',(ROOT/story.OUTPUT/'_invoice-date-task.qmd').read_text())
        self.assertIn('**Check**',(ROOT/story.OUTPUT/'_invoice-date-response.qmd').read_text())
        self.assertNotIn('author:',text.split('---')[1])


if __name__ == '__main__':
    unittest.main()
