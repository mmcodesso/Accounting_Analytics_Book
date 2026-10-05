"""Reconciliation, coverage, and dataset-free provenance for SQL teaching inputs."""
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from scripts.slides.refresh_sql import ASSETS, GENERATORS, check_fresh, query_result

ROOT=Path(__file__).resolve().parents[1]


class SQLSlideTests(unittest.TestCase):
    def facts(self,n):
        return json.loads((ROOT/f'shared/generated/chapter-{n:02}/facts.json').read_text())['queries']

    def test_accounting_controls_reconcile(self):
        f=self.facts(10)
        self.assertAlmostEqual(sum(r[2] for r in f['variance_by_group']['rows']),
                               f['ledger_variance']['rows'][0][0],places=2)
        f=self.facts(11)
        cost=sum(r[1] for r in f['payroll_categories']['rows'] if r[0]!='Employee deductions')
        self.assertAlmostEqual(cost,f['payroll_ledger']['rows'][0][0],places=2)
        f=self.facts(12)
        for _,register,ledger,difference in f['payroll_population']['rows']:
            self.assertAlmostEqual(register,ledger,places=2)
            self.assertEqual(difference,0)

    def test_window_has_consecutive_months_and_equivalent_view(self):
        f=self.facts(11)
        expected=[f'{year}-{month:02}' for year in range(2024,2027) for month in range(1,13)]
        self.assertEqual([r[0] for r in f['hours_by_month']['rows']],expected)
        trailing=f['measure_trailing']['rows']
        self.assertEqual([r[0] for r in trailing],expected[11:])
        self.assertEqual(f['query_view']['rows'],[r for r in trailing if r[0]>='2026-01'])

    def test_read_query_uses_supplied_connection_and_rejects_view_writes(self):
        db=sqlite3.connect(':memory:')
        try:
            db.executescript('CREATE TABLE Account(AccountID,AccountNumber,AccountName);'
                             "INSERT INTO Account VALUES(7,1090,'Clearing'),(8,5080,'Variance'),(9,1000,'Cash');")
            db.execute('PRAGMA query_only=ON')
            result=query_result(db,9,'accounts_by_number')
            self.assertEqual(result['rows'],[(7,1090,'Clearing'),(8,5080,'Variance')])
            with self.assertRaises(ValueError): query_result(db,11,'create_view')
            self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'").fetchone()[0],0)
        finally: db.close()

    def test_dataset_free_freshness_detects_changed_query_and_artifact(self):
        manifest=json.loads((ROOT/'slides/manifest.yml').read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in (*GENERATORS,'_variables.yml'):
                dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
            for chapter in ASSETS:
                shutil.copytree(ROOT/'shared/generated'/chapter,root/'shared/generated'/chapter)
            self.assertFalse((root/'datasets').exists())
            self.assertEqual(check_fresh(root,manifest),[])
            (root/GENERATORS[0]).write_text('# changed query\n')
            (root/'shared/generated/chapter-12/_trace.qmd').write_text('changed evidence')
            errors=check_fresh(root,manifest)
            self.assertTrue(any('shared SQL' in e for e in errors))
            self.assertTrue(any('_trace.qmd' in e for e in errors))


if __name__=='__main__': unittest.main()
