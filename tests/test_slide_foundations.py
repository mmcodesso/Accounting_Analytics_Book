"""Relationship semantics and dataset-free provenance for the foundation decks."""
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from shared.calculations.foundations import relationship
from scripts.slides.refresh_foundations import ASSETS, GENERATORS, check_fresh

ROOT=Path(__file__).resolve().parents[1]


class FoundationTests(unittest.TestCase):
    def test_cardinality_distinguishes_optional_parent_and_multiple_children(self):
        db=sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript('CREATE TABLE Parent (ID INTEGER PRIMARY KEY);'
                        'CREATE TABLE Child (ID INTEGER PRIMARY KEY, ParentID INTEGER);'
                        'INSERT INTO Parent VALUES (1),(2);'
                        'INSERT INTO Child VALUES (10,1),(11,1),(12,NULL);')
        self.assertEqual(relationship(db,'Parent','ID','Child','ParentID'),
                         ('ERzeroToOne','ERzeroToMany'))
        db.execute('DELETE FROM Child WHERE ID IN (11,12)')
        self.assertEqual(relationship(db,'Parent','ID','Child','ParentID'),
                         ('ERmandOne','ERzeroToOne'))
        db.execute('INSERT INTO Child VALUES (13,2)')
        self.assertEqual(relationship(db,'Parent','ID','Child','ParentID'),
                         ('ERmandOne','ERmandOne'))

    def test_facts_validate_without_dataset_and_reject_stale_inputs(self):
        manifest=json.loads((ROOT/'slides/manifest.yml').read_text())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in (*GENERATORS,'_variables.yml'):
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/name,target)
            for chapter in ASSETS:
                shutil.copytree(ROOT/'shared/generated'/chapter,root/'shared/generated'/chapter)
            self.assertFalse((root/'datasets').exists())
            self.assertEqual(check_fresh(root,manifest),[])
            (root/GENERATORS[0]).write_text('# source changed\n')
            artifact=root/'shared/generated/chapter-03/customer-orders.svg'
            artifact.write_text('modified')
            errors=check_fresh(root,manifest)
            self.assertTrue(any('shared source changed' in e for e in errors))
            self.assertTrue(any('customer-orders.svg' in e for e in errors))

    def test_public_invoice_and_shipment_exhibits_reconcile(self):
        facts=json.loads((ROOT/'shared/generated/chapter-03/facts.json').read_text())
        trace=facts['sale_trace']
        self.assertAlmostEqual(sum(r[2] for r in trace['glr']),trace['inv'][5],places=2)
        self.assertAlmostEqual(sum(r[3] for r in trace['glr']),trace['inv'][5],places=2)
        self.assertAlmostEqual(sum(r[2] for r in trace['gls']),trace['shl'][2]*trace['itm'][2],places=2)
        self.assertAlmostEqual(sum(r[3] for r in trace['gls']),trace['shl'][2]*trace['itm'][2],places=2)
        self.assertEqual(facts['relationship_markers']['shipment-invoice'],['ERzeroToOne','ERzeroToOne'])


if __name__=='__main__': unittest.main()
