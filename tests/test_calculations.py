"""The shared calculations behind the book's figures, tested on small in-memory data (no dataset)."""
from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.calculations.bi_ch16 import populations
from shared.calculations.excel_analysis import benford, regression
from shared.calculations.foundations import relationship
from shared.calculations.invoice_margin import invoice_lines


class CalculationTests(unittest.TestCase):
    def test_cardinality_distinguishes_optional_parent_and_multiple_children(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript('CREATE TABLE Parent (ID INTEGER PRIMARY KEY);'
                         'CREATE TABLE Child (ID INTEGER PRIMARY KEY, ParentID INTEGER);'
                         'INSERT INTO Parent VALUES (1),(2);'
                         'INSERT INTO Child VALUES (10,1),(11,1),(12,NULL);')
        self.assertEqual(('ERzeroToOne', 'ERzeroToMany'), relationship(db, 'Parent', 'ID', 'Child', 'ParentID'))
        db.execute('DELETE FROM Child WHERE ID IN (11,12)')
        self.assertEqual(('ERmandOne', 'ERzeroToOne'), relationship(db, 'Parent', 'ID', 'Child', 'ParentID'))
        db.execute('INSERT INTO Child VALUES (13,2)')
        self.assertEqual(('ERmandOne', 'ERmandOne'), relationship(db, 'Parent', 'ID', 'Child', 'ParentID'))

    def test_populations_count_each_process_read_only(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript('CREATE TABLE JournalEntry(ID); INSERT INTO JournalEntry VALUES(1);'
                         'CREATE TABLE PurchaseOrder(ID); INSERT INTO PurchaseOrder VALUES(1),(2);'
                         'CREATE TABLE PayrollRegister(ID);')
        db.execute('PRAGMA query_only=ON')
        self.assertEqual({'Journal entries': 1, 'Purchase orders': 2, 'Payroll': 0}, populations(db))

    def test_first_digits_cover_small_and_large_amounts(self):
        result = benford([.012, 2, 30, 400, 5000, 60000, 7, 80, 900])
        self.assertEqual({i: 1 for i in range(1, 10)}, dict(result['counts']))
        self.assertAlmostEqual(1, sum(result['expected'].values()))

    def test_regression_reports_the_toolpak_quantities(self):
        xs = [1, 2, 3, 4, 5]
        ys = [3, 5, 4, 7, 9]
        fit = regression(xs, ys)
        # Least squares by hand: slope 1.4, intercept 1.4, R squared 0.8448 (SSR 19.6 of SST 23.2).
        self.assertAlmostEqual(1.4, fit['b'])
        self.assertAlmostEqual(1.4, fit['a'])
        self.assertAlmostEqual(19.6 / 23.2, fit['r2'])
        self.assertEqual(3, fit['df'])
        self.assertAlmostEqual(fit['ssr'] / (fit['sse'] / fit['df']), fit['f'])

    def test_invoice_lines_keep_unrounded_extended_cost(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / 'example.sqlite'
            writer = sqlite3.connect(database)
            writer.executescript("""
                CREATE TABLE SalesInvoiceLine (SalesInvoiceLineID, SalesInvoiceID, ItemID,
                    Quantity, BaseListPrice, UnitPrice, Discount, LineTotal, PromotionID);
                CREATE TABLE SalesInvoice (SalesInvoiceID, InvoiceDate, CustomerID);
                CREATE TABLE Item (ItemID, ItemGroup, StandardCost);
                CREATE TABLE Customer (CustomerID, CustomerSegment);
                INSERT INTO Customer VALUES (1, 'Wholesale');
                INSERT INTO SalesInvoice VALUES (1, '2026-01-02', 1);
                INSERT INTO Item VALUES (1, 'Furniture', 25.001);
                INSERT INTO SalesInvoiceLine VALUES (1,1,1,2,60,50,0,100,NULL);
            """)
            writer.commit()
            writer.close()
            connection = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
            try:
                line = invoice_lines(connection)[0]
                self.assertEqual(50.002, line['C'])
                self.assertEqual('2026-Q1', line['per'])
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute('DELETE FROM SalesInvoiceLine')
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
