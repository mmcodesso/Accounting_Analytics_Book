"""The one-command build (scripts/build_everything.py): its stages and units follow the companion manifest, each unit
names the files the Downloads page links, a builder's inputs follow its imports, and the decision to run a unit
(never recorded, an input changed, an output missing, forced) is right. Nothing here builds anything or needs the
dataset, Office, Quarto or the network; the decision tests build a small git repository and are skipped without git."""
from __future__ import annotations

import argparse
import contextlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_everything as be

HAS_GIT = shutil.which('git') is not None


def namespace(**overrides) -> argparse.Namespace:
    values = dict(plan=False, list=False, only=None, skip=None, from_stage=None, force=None, no_office=False,
                  print=False, publish=False, publish_dry_run=False, adopt=False, trust=False, ignore_newer=[])
    values.update(overrides)
    return argparse.Namespace(**values)


def units_by_key(stages) -> dict[str, be.Unit]:
    return {unit.key: unit for stage in stages for unit in stage.units}


class StagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import yaml
        cls.manifest = yaml.safe_load(be.MANIFEST.read_text(encoding='utf-8'))
        cls.stages = be.build_stages(namespace())
        cls.units = units_by_key(cls.stages)

    def test_stages_come_in_the_documented_order(self) -> None:
        self.assertEqual([s.name for s in self.stages], list(be.STAGE_ORDER))
        self.assertEqual(set(be.STAGE_TITLES), set(be.STAGE_ORDER))
        names = [u.name for s in self.stages for u in s.units]
        self.assertEqual(len(names), len(set(names)), 'a unit name appears twice')

    def test_every_manifest_entry_has_a_unit(self) -> None:
        for entry in self.manifest['solutions']:
            self.assertIn(f'solution:{entry["id"]}', self.units, entry['id'])
            self.assertEqual(self.units[f'solution:{entry["id"]}'].stage, f'companion-{entry["tool"]}')
        for chain in self.manifest['chains']:
            if chain['tool'] != 'pbi':
                self.assertIn(f'chain:{chain["id"]}', self.units, chain['id'])
        pbi = [u for u in self.units.values() if u.key.startswith('chains:')]
        self.assertEqual(len(pbi), 1, 'the Power BI chains are one unit')
        for chain in self.manifest['chains']:
            if chain['tool'] == 'pbi':
                self.assertIn(chain['id'], pbi[0].key)

    def test_commands_name_scripts_and_ids_that_exist(self) -> None:
        ids = {e['id'] for e in self.manifest['solutions']}
        for unit in self.units.values():
            for command in unit.commands:
                script = ROOT / command[1] if len(command) > 1 and not command[1].startswith('-') else None
                if script is not None:
                    self.assertTrue(script.is_file(), f'{unit.name}: {command[1]}')
                if '--id' in command:
                    self.assertIn(command[command.index('--id') + 1], ids, unit.name)

    def test_outputs_are_the_files_the_downloads_page_links(self) -> None:
        links = set(re.findall(r'\]\(/supplementary/([^)\s]+)\)',
                               (ROOT / 'front-matter/downloads.qmd').read_text(encoding='utf-8')))
        for unit in self.units.values():
            if not unit.stage.startswith('companion'):
                continue
            for output in unit.outputs:
                folder, name = output.rsplit('/', 2)[-2:]
                self.assertIn(f'{folder}/{name}', links, f'{unit.name}: {output}')

    def test_office_units_are_marked(self) -> None:
        self.assertEqual({u.key for u in self.units.values() if u.office == 'excel'},
                         {u.key for u in self.units.values() if u.stage == 'companion-excel'})
        self.assertEqual({u.key for u in self.units.values() if u.office == 'pbi'},
                         {u.key for u in self.units.values() if u.stage == 'companion-pbi'})
        self.assertTrue(all(u.office is None for u in self.units.values() if u.stage == 'companion-sql'))


class InputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.units = units_by_key(be.build_stages(namespace()))

    def paths(self, key: str) -> set[str]:
        return set(self.units[key].inputs.paths)

    def test_a_builder_is_an_input_of_its_own_unit_only(self) -> None:
        ex07 = 'scripts/companion/xlbuild/ex07.py'
        self.assertIn(ex07, self.paths('solution:ch07-exercises'))
        for key in ('solution:ch09-exercises-sql', 'solution:ch13-exercises-pbi', 'solution:ch04-exercises'):
            self.assertNotIn(ex07, self.paths(key), key)

    def test_imports_are_followed_through_the_repository(self) -> None:
        paths = self.paths('solution:ch07-exercises')
        self.assertIn('scripts/companion/xlbuild/analysis.py', paths)       # ex07 imports it
        self.assertIn('scripts/companion/xlbuild/notes.py', paths)          # companion/build.py imports it
        self.assertIn('scripts/paths.py', paths)

    def test_notes_templates_follow_a_notes_module(self) -> None:
        paths = be.closure(('scripts/companion/xlbuild/ex07.py',))
        modules = [p for p in paths if p.startswith('facts/notes/') and p.endswith('.py') and '/templates/' not in p]
        for module in modules:
            stem = Path(module).stem
            if (ROOT / 'facts/notes/templates' / stem).is_dir():
                self.assertIn(f'facts/notes/templates/{stem}', paths, module)

    def test_a_solution_depends_on_the_chain_it_starts_from(self) -> None:
        inputs = self.units['solution:ch07-exercises'].inputs
        self.assertIn('outputs/companion/start-files/Chapter07-companion.zip', inputs.sigs)
        self.assertIn('scripts/companion/xlbuild/analysis.py', inputs.paths)

    def test_a_unit_does_not_depend_on_its_own_output(self) -> None:
        inputs = self.units['solution:ch19-capstone-pbi'].inputs
        self.assertFalse([s for s in inputs.sigs if 'Chapter19-capstone-pbi/' in s], 'RefundFlags.csv is its own output')
        inputs = self.units['solution:ch18-capstone-pbi'].inputs
        self.assertIn('outputs/companion/solutions/Chapter18-capstone-excel/Make Buy Reprice.xlsx', inputs.sigs)

    def test_the_guides_do_not_read_what_the_figure_build_writes(self) -> None:
        for key in ('build', 'render-check'):
            paths = self.paths(key)
            self.assertNotIn('facts/instructor', paths)
            self.assertNotIn('facts/instructor/figures', paths)
            self.assertFalse([s for s in self.units[key].inputs.sigs if 'Instructor-Notes' in s])
        self.assertIn('instructor-notes/figures', self.paths('render-check'))
        self.assertNotIn('instructor-notes/figures', self.paths('build'))


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stages = be.build_stages(namespace())

    def select(self, **overrides) -> list[str]:
        return [u.name for u in be.select_units(be.build_stages(namespace(**overrides)), namespace(**overrides))]

    def test_opt_in_stages_are_left_out_by_default(self) -> None:
        stages = {n.split('/')[0] for n in self.select()}
        self.assertFalse(stages & {'print', 'publish'})
        self.assertIn('print', {n.split('/')[0] for n in self.select(print=True)})
        self.assertIn('publish', {n.split('/')[0] for n in self.select(publish=True)})
        self.assertIn('publish', {n.split('/')[0] for n in self.select(publish_dry_run=True)})

    def test_only_skip_and_from(self) -> None:
        self.assertEqual(self.select(only=['guides']), ['guides/render-check'])
        self.assertEqual(self.select(only=['guides/render-check']), ['guides/render-check'])
        self.assertEqual(self.select(only=['solution:ch07-exercises']), ['companion-excel/solution:ch07-exercises'])
        self.assertNotIn('companion-excel/solution:ch07-exercises', self.select(skip=['companion-excel']))
        names = self.select(from_stage='book')
        self.assertEqual(names[0], 'book/book-and-decks')
        self.assertNotIn('gates/fast-checks', names)
        self.assertEqual(self.select(only=['print']), ['print/interiors'])      # naming an opt-in stage runs it

    def test_unknown_names_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            self.select(only=['no-such-stage'])
        with self.assertRaises(ValueError):
            self.select(from_stage='no-such-stage')


@unittest.skipUnless(HAS_GIT, 'git is not installed')
class DecisionTests(unittest.TestCase):
    """plan_unit in a small repository: never recorded, current, an input changed, an output missing, forced."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        for name, text in (('a.txt', 'one'), ('out.txt', 'built')):
            (self.root / name).write_text(text, encoding='utf-8')
        self.git('init', '-q')
        self.git('add', '--all')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-q', '-m', 'first')
        self.original = (be.ROOT, be.release.ROOT)
        be.ROOT = self.root                       # signature(), output_exists() and snapshot() read this module's ROOT
        self.addCleanup(self.restore)

    def restore(self) -> None:
        be.ROOT = self.original[0]

    def git(self, *args: str) -> str:
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()

    def context(self, store: dict | None = None) -> be.Context:
        ctx = be.Context(store or {'units': {}})
        ctx._tree = self.git('write-tree')
        return ctx

    def unit(self, **kw) -> be.Unit:
        return be.Unit('u', 'stage', 'a unit', commands=[['run']], inputs=be.Inputs(paths=['a.txt'], tokens={'t': '1'}),
                       outputs=('out.txt',), **kw)

    def recorded(self, unit: be.Unit) -> dict:
        return {'units': {unit.name: {'snapshot': be.snapshot(unit.inputs, self.context()._tree)}}}

    def test_an_unrecorded_unit_runs(self) -> None:
        plan = be.plan_unit(self.unit(), self.context(), False)
        self.assertEqual(plan.commands, [['run']])
        self.assertEqual(plan.reason, 'not recorded as built')

    def test_a_recorded_unit_with_nothing_changed_is_current(self) -> None:
        unit = self.unit()
        plan = be.plan_unit(unit, self.context(self.recorded(unit)), False)
        self.assertEqual((plan.commands, plan.reason), ([], 'current'))

    def test_a_changed_file_a_changed_token_and_a_missing_output_run_it(self) -> None:
        unit = self.unit()
        store = self.recorded(unit)
        (self.root / 'a.txt').write_text('a longer second version', encoding='utf-8')
        self.git('add', '--all')
        plan = be.plan_unit(unit, self.context(store), False)
        self.assertTrue(plan.commands)
        self.assertEqual(plan.reason, 'changed: a.txt')
        (self.root / 'a.txt').write_text('one', encoding='utf-8')
        self.git('add', '--all')
        self.assertFalse(be.plan_unit(unit, self.context(store), False).commands)
        unit.inputs.tokens['t'] = '2'
        self.assertEqual(be.plan_unit(unit, self.context(store), False).reason, 'changed: t')
        unit.inputs.tokens['t'] = '1'
        (self.root / 'out.txt').unlink()
        self.assertEqual(be.plan_unit(unit, self.context(store), False).reason, 'missing out.txt')

    def test_force_runs_a_current_unit(self) -> None:
        unit = self.unit()
        plan = be.plan_unit(unit, self.context(self.recorded(unit)), True)
        self.assertEqual((plan.commands, plan.reason), ([['run']], 'forced'))

    def test_a_cheap_unit_runs_every_time(self) -> None:
        unit = be.Unit('cheap', 'stage', 'cheap', commands=[['run']], always=True)
        self.assertEqual(be.plan_unit(unit, self.context(), False).reason, 'runs every time')

    def test_a_file_outside_git_is_compared_by_size_and_time(self) -> None:
        (self.root / 'ignored.bin').write_bytes(b'12')
        unit = be.Unit('u', 'stage', 'a unit', commands=[['run']], inputs=be.Inputs(sigs=['ignored.bin']), outputs=('out.txt',))
        store = {'units': {unit.name: {'snapshot': be.snapshot(unit.inputs, self.context()._tree)}}}
        self.assertFalse(be.plan_unit(unit, self.context(store), False).commands)
        (self.root / 'ignored.bin').write_bytes(b'123')
        self.assertEqual(be.plan_unit(unit, self.context(store), False).reason, 'changed: ignored.bin')


@unittest.skipUnless(HAS_GIT, 'git is not installed')
class RunTests(unittest.TestCase):
    """run_units in a small repository, with commands that are one line of Python."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        (self.root / 'a.txt').write_text('one', encoding='utf-8')
        self.git('init', '-q')
        self.git('add', '--all')
        self.git('-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-q', '-m', 'first')
        self.saved = (be.ROOT, be.LOG, be.STORE)
        be.ROOT, be.LOG, be.STORE = self.root, self.root / 'log/run.log', self.root / 'log/store.json'
        self.addCleanup(self.restore)

    def restore(self) -> None:
        be.ROOT, be.LOG, be.STORE = self.saved

    def git(self, *args: str) -> str:
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()

    def python(self, code: str) -> list[str]:
        return [sys.executable, '-c', code]

    def run_units(self, units: list[be.Unit], **overrides) -> list[be.Result]:
        with contextlib.redirect_stdout(io.StringIO()):
            return be.run_units(units, namespace(**overrides))

    def test_a_failed_step_stops_the_run(self) -> None:
        failing = be.Unit('fails', 's', 'fails', commands=[self.python('import sys; sys.exit(3)')], always=True)
        after = be.Unit('after', 's', 'after', commands=[self.python('pass')], always=True)
        results = self.run_units([failing, after])
        self.assertEqual([(r.unit.key, r.status) for r in results], [('fails', 'failed')])
        self.assertIn('exited with 3', results[0].detail)

    def test_an_intermittent_windows_error_is_retried_once(self) -> None:
        code = ("import pathlib, sys\np = pathlib.Path('tried.txt')\n"
                "if not p.exists():\n    p.write_text('1')\n    print('OSError: [Errno 22] Invalid argument')\n    sys.exit(1)\n")
        unit = be.Unit('flaky', 's', 'flaky', commands=[self.python(code)], always=True, retries=1)
        self.assertEqual([r.status for r in self.run_units([unit])], ['built'])
        (self.root / 'tried.txt').unlink()
        other = be.Unit('other', 's', 'other', commands=[self.python(code.replace('Errno 22', 'something else'))], always=True,
                        retries=1)
        self.assertEqual([r.status for r in self.run_units([other])], ['failed'])

    def test_a_unit_is_recorded_then_skipped_then_rebuilt_when_an_input_changes(self) -> None:
        unit = be.Unit('u', 's', 'a unit', commands=[self.python("open('out.txt', 'w').write('x')")],
                       inputs=be.Inputs(paths=['a.txt']), outputs=('out.txt',))
        self.assertEqual([r.status for r in self.run_units([unit])], ['built'])
        self.assertTrue((self.root / 'out.txt').is_file())
        self.assertEqual([r.status for r in self.run_units([unit])], ['current'])
        (self.root / 'a.txt').write_text('a longer second version', encoding='utf-8')
        results = self.run_units([unit])
        self.assertEqual([r.status for r in results], ['built'])
        self.assertEqual(results[0].detail, 'changed: a.txt')
        self.assertEqual([r.status for r in self.run_units([unit])], ['current'])
        self.assertEqual([r.status for r in self.run_units([unit], force=['all'])], ['built'])

    def test_a_unit_whose_inputs_move_while_it_runs_is_not_recorded(self) -> None:
        unit = be.Unit('u', 's', 'a unit', commands=[self.python("open('a.txt', 'w').write('moved')")],
                       inputs=be.Inputs(paths=['a.txt']))
        self.assertEqual([r.status for r in self.run_units([unit])], ['built'])
        self.assertEqual([r.status for r in self.run_units([unit])], ['built'], 'it was never recorded, so it runs again')

    def test_plan_mode_runs_nothing(self) -> None:
        unit = be.Unit('u', 's', 'a unit', commands=[self.python("open('out.txt', 'w').write('x')")],
                       inputs=be.Inputs(paths=['a.txt']), outputs=('out.txt',))
        results = self.run_units([unit], plan=True)
        self.assertEqual([r.status for r in results], ['planned'])
        self.assertFalse((self.root / 'out.txt').exists())

    def test_publishing_needs_a_clean_tree(self) -> None:
        (self.root / 'new.txt').write_text('uncommitted', encoding='utf-8')
        ctx = be.Context({'units': {}})
        with self.assertRaises(ValueError):
            be.publish_plan_for(False)(ctx, False)
        plan = be.publish_plan_for(True)(ctx, False)                 # a dry run needs no commit
        self.assertEqual(plan.commands[0][-2:], ['publish', '--dry-run'])

    def test_no_office_leaves_those_units_out(self) -> None:
        unit = be.Unit('excel', 's', 'excel', commands=[self.python('raise SystemExit(9)')], always=True, office='excel')
        results = self.run_units([unit], no_office=True)
        self.assertEqual([(r.status, r.detail) for r in results], [('skipped', '--no-office')])


class PlanTests(unittest.TestCase):
    @unittest.skipUnless(HAS_GIT, 'git is not installed')
    def test_list_and_plan_run_without_building_anything(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(be.main(['--list']), 0)
            self.assertEqual(be.main(['--plan', '--no-office']), 0)
        self.assertIn('companion-excel', out.getvalue())
        self.assertIn('Plan:', out.getvalue())

    @unittest.skipUnless(HAS_GIT, 'git is not installed')
    def test_every_units_forced_plan_is_a_list_of_commands(self) -> None:
        """Including the opt-in print and publish units, which a default run never plans."""
        args = namespace(print=True, publish_dry_run=True)
        ctx = be.Context({'units': {}})
        count = 0
        for stage in be.build_stages(args):
            for unit in stage.units:
                plan = be.plan_unit(unit, ctx, True)
                self.assertTrue(plan.commands, unit.name)
                for command in plan.commands:
                    self.assertIsInstance(command, list, unit.name)
                    self.assertTrue(all(isinstance(part, str) for part in command), f'{unit.name}: {command}')
                    self.assertTrue(be.shown(command), unit.name)
                count += 1
        self.assertGreater(count, 40)

    def test_the_readme_describes_the_script(self) -> None:
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('python scripts/build_everything.py', readme)
        for flag in ('--plan', '--only', '--force', '--no-office', '--publish', '--adopt'):
            self.assertIn(flag, readme)


if __name__ == '__main__':
    unittest.main()
