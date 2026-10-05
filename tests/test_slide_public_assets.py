"""Meaningful checks for shared measures, provenance, and public figure assets."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.calculations.invoice_margin import invoice_lines, quarterly_margin
from scripts.slides.refresh import ASSET_NAMES, GENERATORS, OUTPUT, check_fresh


class PublicMeasuresTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "outputs/build/tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_readonly_measures_preserve_unrounded_weighted_margin(self):
        database = self.root / "example.sqlite"
        writer = sqlite3.connect(database)
        writer.executescript("""
            CREATE TABLE SalesInvoiceLine (SalesInvoiceLineID, SalesInvoiceID, ItemID,
                Quantity, BaseListPrice, UnitPrice, Discount, LineTotal, PromotionID);
            CREATE TABLE SalesInvoice (SalesInvoiceID, InvoiceDate, CustomerID);
            CREATE TABLE Item (ItemID, ItemGroup, StandardCost);
            CREATE TABLE Customer (CustomerID, CustomerSegment);
            INSERT INTO Customer VALUES (1, 'Retail');
            INSERT INTO SalesInvoice VALUES (1, '2026-01-02', 1);
            INSERT INTO SalesInvoice VALUES (2, '2026-04-02', 1);
            INSERT INTO Item VALUES (1, 'Furniture', 25.001);
            INSERT INTO Item VALUES (2, 'Furniture', 10);
            INSERT INTO SalesInvoiceLine VALUES (1,1,1,2,60,50,0,100,NULL);
            INSERT INTO SalesInvoiceLine VALUES (2,1,2,1,900,900,0,900,NULL);
            INSERT INTO SalesInvoiceLine VALUES (3,2,2,1,0,0,0,0,NULL);
        """)
        writer.commit()
        writer.close()
        connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
        self.addCleanup(connection.close)
        lines = invoice_lines(connection)
        self.assertEqual(lines[0]["C"], 50.002)
        quarters = quarterly_margin(connection, 2026, "Furniture")
        self.assertAlmostEqual(quarters[0]["margin_rate"], (1000 - 60.002) / 1000)
        self.assertEqual(quarters[0]["invoice_lines"], 2)
        self.assertIsNone(quarters[1]["margin_rate"])
        self.assertIsNone(quarters[2]["margin_rate"])
        with self.assertRaises(sqlite3.OperationalError):
            connection.execute("DELETE FROM SalesInvoiceLine")

    def _public_checkout(self):
        for name in (*GENERATORS, "_variables.yml"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        shutil.copytree(ROOT / OUTPUT, self.root / OUTPUT)
        self.assertFalse((self.root / "datasets").exists())

    def test_committed_public_artifacts_validate_without_dataset(self):
        self._public_checkout()
        self.assertEqual(check_fresh(self.root), [])

    def test_windows_newlines_preserve_source_and_artifact_freshness(self):
        self._public_checkout()
        for name in (*GENERATORS, str(OUTPUT / "_furniture-table.qmd"),
                     str(OUTPUT / "workflow.svg"), str(OUTPUT / "furniture-margin.csv")):
            path = self.root / name
            text = path.read_text(encoding="utf-8")
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(check_fresh(self.root), [])

    def test_stale_generator_and_modified_asset_are_rejected(self):
        self._public_checkout()
        (self.root / GENERATORS[0]).write_text("# changed source\n", encoding="utf-8")
        (self.root / OUTPUT / "workflow.svg").write_text("changed", encoding="utf-8")
        errors = check_fresh(self.root)
        self.assertTrue(any("source changed" in error for error in errors), errors)
        self.assertTrue(any("workflow.svg" in error for error in errors), errors)

    def test_new_dataset_pin_requires_refresh(self):
        self._public_checkout()
        variables = self.root / "_variables.yml"
        text = variables.read_text(encoding="utf-8").replace('version: "v2026.1"', 'version: "v2027.1"')
        variables.write_text(text, encoding="utf-8")
        self.assertTrue(any("pinned dataset" in error for error in check_fresh(self.root)))

    def test_public_asset_accessibility_and_trace_values(self):
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        for name in ASSET_NAMES:
            svg = ET.parse(ROOT / OUTPUT / f"{name}.svg").getroot()
            self.assertTrue(svg.find("svg:title", namespace).text)
            self.assertTrue(svg.find("svg:desc", namespace).text)
            png = (ROOT / OUTPUT / f"{name}.png").read_bytes()
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(int.from_bytes(png[16:20], "big"), 2560)
        facts = json.loads((ROOT / OUTPUT / "facts.json").read_text(encoding="utf-8"))
        trace = facts["source_trace"]
        self.assertEqual((trace["gl_entry_id"], trace["invoice_id"], trace["invoice_line_id"]),
                         (126312, 7947, 10645))
        self.assertEqual(trace["quantity"] * trace["unit_price"], 688.42)
        self.assertEqual(trace["credit"], trace["line_total"])
        self.assertEqual([round(q["margin_rate"] * 100, 2) for q in facts["furniture_quarters"][-2:]],
                         [42.26, 40.78])


if __name__ == "__main__":
    unittest.main()
