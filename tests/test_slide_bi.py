"""Dataset-free controls for the public Power BI teaching exhibits."""
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from scripts.slides.refresh_bi import ASSETS, GENERATORS, check_fresh
from shared.calculations.bi_ch16 import populations

ROOT=Path(__file__).resolve().parents[1]


class PowerBISlideTests(unittest.TestCase):
    def facts(self,n):
        return json.loads((ROOT/f'shared/generated/chapter-{n}/facts.json').read_text())['public_examples']

    def test_restructure_preserves_count_and_revenue(self):
        before=self.facts(13);after=self.facts(14)
        self.assertEqual(before['profile_all']['n'],after['source_rows'])
        self.assertEqual(after['source_rows'],after['merged_rows'])
        self.assertAlmostEqual(after['source_revenue'],after['merged_revenue'],places=2)
        for values in after['income'].values():
            self.assertAlmostEqual(values['all'],0,places=2)
            self.assertGreater(values['open'],0)

    def test_budget_explanation_reconciles_at_company_and_department(self):
        f=self.facts(15);t=f['budget_totals']
        self.assertAlmostEqual(t['actual']-t['budget'],t['variance'],places=2)
        self.assertAlmostEqual(t['variance'],t['volume']+t['classification']+t['remaining'],places=2)
        self.assertAlmostEqual(t['classification'],0,places=2)
        for row in f['budget']['rows'].values():
            self.assertAlmostEqual(row['variance'],row['volume']+(row['classification'] or 0)+row['remaining'],places=2)

    def test_visual_window_agrees_only_when_history_matches(self):
        f=self.facts(15)['window']
        self.assertEqual(f['months'],[f'2026-{m:02}' for m in range(1,13)])
        self.assertNotAlmostEqual(f['model_history'][0],f['visible_axis'][0],places=2)
        self.assertAlmostEqual(f['model_history'][-1],f['visible_axis'][-1],places=10)
        sql=json.loads((ROOT/'shared/generated/chapter-11/facts.json').read_text())['queries']['query_view']['rows']
        for index,row in enumerate(sql):
            self.assertEqual(row[0],f['months'][index])
            self.assertAlmostEqual(row[4],round(f['model_history'][index],2),places=2)

    def test_register_counts_preserve_failures_and_review_partition(self):
        f=self.facts(16)
        self.assertEqual(sum(f['counts'].values()),f['exceptions'])
        self.assertLess(f['distinct_documents'],f['exceptions'])
        self.assertEqual(sum(f['dispositions'].values()),f['exceptions'])
        self.assertGreater(f['dispositions']['Open'],0)
        db=sqlite3.connect(':memory:')
        try:
            db.executescript('CREATE TABLE JournalEntry(ID); INSERT INTO JournalEntry VALUES(1);'
                             'CREATE TABLE PurchaseOrder(ID); INSERT INTO PurchaseOrder VALUES(1),(2);'
                             'CREATE TABLE PayrollRegister(ID);')
            db.execute('PRAGMA query_only=ON')
            self.assertEqual(populations(db),{'Journal entries':1,'Purchase orders':2,'Payroll':0})
        finally: db.close()

    def test_freshness_detects_changed_calculation_and_graphic_without_data(self):
        manifest=json.loads((ROOT/'slides/manifest.yml').read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in (*GENERATORS,'_variables.yml'):
                out=root/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,out)
            for chapter in ASSETS:
                shutil.copytree(ROOT/'shared/generated'/chapter,root/'shared/generated'/chapter)
            self.assertFalse((root/'datasets').exists())
            self.assertEqual(check_fresh(root,manifest),[])
            (root/GENERATORS[0]).write_text('# changed calculation\n')
            (root/'shared/generated/chapter-14/star.svg').write_text('<svg/>')
            errors=check_fresh(root,manifest)
            self.assertTrue(any('shared Power BI source' in e for e in errors))
            self.assertTrue(any('star.svg' in e for e in errors))


if __name__=='__main__':unittest.main()
