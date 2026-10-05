"""Meaningful reconciliations and source-freshness checks for Excel decks."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from shared.calculations.excel_analysis import benford, regression
from scripts.slides.refresh_excel import ASSETS, GENERATORS, check_fresh

ROOT=Path(__file__).resolve().parents[1]


class ExcelSlideTests(unittest.TestCase):
    def facts(self, chapter):
        return json.loads((ROOT/f'shared/generated/chapter-{chapter:02d}/facts.json').read_text())

    def test_margin_and_budget_bridges_reconcile(self):
        bridge=self.facts(6)['bridge']
        self.assertAlmostEqual(bridge['q3']+sum(bridge[k] for k in
            ['volume','mix','price lists','promotions','cost']),bridge['q4'],places=2)
        budget=self.facts(7)['budget']
        volume=budget['flex']-budget['static'];remaining=budget['actual']-budget['flex']
        self.assertAlmostEqual(budget['static']+volume+remaining,budget['actual'],places=2)
        model=self.facts(7)['model']
        contribution=model['units']*(1+model['breakeven'])*(model['price']*.9*(1-model['rate'])-model['cost'])
        self.assertAlmostEqual(contribution,model['without'],places=2)

    def test_backtest_keeps_test_months_out_of_fit(self):
        facts=self.facts(7);ys=[v for _,v in facts['monthly']]
        fit=regression(list(range(2,34)),ys[1:33])
        self.assertEqual(facts['backtest']['actual'],ys[33:])
        forecast=dict(facts['backtest']['methods'])['Trend']
        self.assertEqual(forecast,[fit['a']+fit['b']*x for x in (34,35,36)])
        # Changing only the held-out actual values must not alter those forecasts.
        changed=ys[:33]+[v*10 for v in ys[33:]]
        refit=regression(list(range(2,34)),changed[1:33])
        self.assertEqual(fit,refit)

    def test_digit_and_aging_populations_reconcile(self):
        result=benford([.012,2,30,400,5000,60000,7,80,900])
        self.assertEqual(dict(result['counts']),{i:1 for i in range(1,10)})
        self.assertAlmostEqual(sum(result['expected'].values()),1)
        facts=self.facts(8)
        self.assertEqual(facts['benford']['Full payments']['n']+facts['benford']['Partial payments']['n'],facts['payment_count'])
        aging=facts['aging']
        self.assertAlmostEqual(sum(row[1] for row in aging['buckets'].values()),aging['subledger'],places=2)
        self.assertAlmostEqual(sum(aging['ledger'].values()),aging['gl'],places=2)

    def test_dataset_free_freshness_rejects_changed_source_and_artifact(self):
        manifest=json.loads((ROOT/'slides/manifest.yml').read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in (*GENERATORS,'_variables.yml'):
                dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
            for chapter in ASSETS:
                shutil.copytree(ROOT/'shared/generated'/chapter,root/'shared/generated'/chapter)
            self.assertFalse((root/'datasets').exists())
            self.assertEqual(check_fresh(root,manifest),[])
            (root/GENERATORS[0]).write_text('# changed calculation\n')
            (root/'shared/generated/chapter-07/_backtest.qmd').write_text('changed values')
            errors=check_fresh(root,manifest)
            self.assertTrue(any('shared source changed' in e for e in errors))
            self.assertTrue(any('_backtest.qmd' in e for e in errors))


if __name__=='__main__': unittest.main()
