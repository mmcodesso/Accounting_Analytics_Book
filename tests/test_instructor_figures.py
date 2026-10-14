"""Tests for scripts/figures/instructor: the figure build's manifest logic and the layout kit (no Draw.io, no dataset)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
for p in (REPO / "scripts" / "figures" / "instructor", REPO / "scripts" / "figures", REPO / "facts" / "instructor",
          REPO / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import build_instructor as build  # noqa: E402
import guides  # noqa: E402
import kit  # noqa: E402
from drawio import Diagram  # noqa: E402
from manifest import Manifest, digest_file, digest_text_file  # noqa: E402

TEMPLATE = """---
title: Example
kind: exercise
number: '1.1'
unit: '1'
perspective: general
tool: conceptual
minutes: 30
solution: ''
figures:
  - {id: IF-01-1-A, kind: diagram, purpose: A flow., shows: Boxes., data: None.}
  - {id: IF-C2-0-A, kind: excel-mock, purpose: The sheet., shows: Cells., data: None.}
---
# Exercise 1.1
"""


class UnitTests(unittest.TestCase):
    def test_unit_codes(self):
        self.assertEqual(build.normalize_unit("6"), "06")
        self.assertEqual(build.normalize_unit("06"), "06")
        self.assertEqual(build.normalize_unit("case2"), "C2")
        self.assertEqual(build.normalize_unit("appB"), "AB")
        self.assertEqual(build.normalize_unit("AB"), "AB")

    def test_figure_id_pattern(self):
        for good in ("IF-06-1-A", "IF-C4-0-B", "IF-AB-2-C", "IF-19-10-A"):
            self.assertTrue(build.ID.match(good), good)
        for bad in ("IF-6-1-A", "IF-06-1-a", "IF-06-A", "fig-06-01"):
            self.assertFalse(build.ID.match(bad), bad)

    def test_declared_and_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            guides_dir = Path(tmp)
            (guides_dir / "chapter-01-role").mkdir()
            (guides_dir / "case-part-2").mkdir()
            (guides_dir / "appendix-b-security").mkdir()
            (guides_dir / "chapter-01-role" / "ex-1.1-example.md").write_text(TEMPLATE, encoding="utf-8")
            found = build.declared(guides_dir)
            self.assertEqual(set(found), {"IF-01-1-A", "IF-C2-0-A"})
            self.assertEqual(found["IF-01-1-A"].code, "01")
            self.assertEqual(build.folder_of("01", guides_dir), "chapter-01-role")
            self.assertEqual(build.folder_of("C2", guides_dir), "case-part-2")
            self.assertEqual(build.folder_of("AB", guides_dir), "appendix-b-security")
            self.assertIsNone(build.folder_of("07", guides_dir))

    def test_duplicate_id_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "chapter-01-role"
            folder.mkdir()
            (folder / "a.md").write_text(TEMPLATE, encoding="utf-8")
            (folder / "b.md").write_text(TEMPLATE, encoding="utf-8")
            with self.assertRaises(ValueError):
                build.declared(Path(tmp))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.patches = [mock.patch.object(build, "SRC", root / "src"), mock.patch.object(build, "OUT", root / "out")]
        for patch in self.patches:
            patch.start()
        self.fig = build.Figure("IF-01-1-A", "01", "chapter-01-role", "x.md", "diagram", "p", "s", "d")
        self.module = root / "fig_01.py"
        self.module.write_text("FIGURES = {}\n", encoding="utf-8")
        self.manifest = Manifest(root / "out" / "manifest.json")

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.tmp.cleanup()

    def write_built(self):
        self.fig.source.parent.mkdir(parents=True)
        self.fig.source.write_text("<mxfile/>\n", encoding="utf-8")
        self.fig.pdf.parent.mkdir(parents=True)
        self.fig.pdf.write_bytes(b"%PDF-1.4 fake")
        self.manifest.record(self.fig.id, self.fig.folder, self.fig.source, self.module, self.fig.pdf)

    def test_states(self):
        self.assertEqual(build.state(self.fig, self.manifest), "planned")
        self.write_built()
        self.assertEqual(build.state(self.fig, self.manifest), "current")
        self.fig.source.write_text("<mxfile>changed</mxfile>\n", encoding="utf-8")
        self.assertEqual(build.state(self.fig, self.manifest), "stale")

    def test_line_endings_do_not_make_a_source_stale(self):
        self.write_built()
        self.fig.source.write_bytes(b"<mxfile/>\r\n")
        self.assertEqual(build.state(self.fig, self.manifest), "current")

    def test_a_replaced_pdf_is_stale(self):
        self.write_built()
        self.fig.pdf.write_bytes(b"%PDF-1.4 other")
        self.assertEqual(build.state(self.fig, self.manifest), "stale")

    def test_manifest_round_trip(self):
        self.write_built()
        self.manifest.save({"scale": 1.5})
        again = Manifest(self.manifest.path)
        self.assertEqual(again.entry("IF-01-1-A")["pdf_sha256"], digest_file(self.fig.pdf))
        self.assertEqual(again.entry("IF-01-1-A")["generator"], digest_text_file(self.module))
        self.assertEqual(again.settings, {"scale": 1.5})

    def test_select(self):
        figures = {"IF-01-1-A": self.fig,
                   "IF-C2-0-A": build.Figure("IF-C2-0-A", "C2", "case-part-2", "x.md", "diagram", "", "", "")}
        self.assertEqual([f.id for f in build.select(figures, ["case2"], None)], ["IF-C2-0-A"])
        self.assertEqual([f.id for f in build.select(figures, None, ["IF-01"])], ["IF-01-1-A"])
        self.assertEqual(len(build.select(figures, None, None)), 2)


class KitTests(unittest.TestCase):
    def test_flow_row_fits_the_frame_and_links_every_node(self):
        d = Diagram("test")
        shot = kit.flow(d, [("A", "first"), ("B", "second"), "C"], gap=40, labels=["x", None])
        self.assertEqual(len(shot["ids"]), 3)
        last = shot["boxes"][-1]
        self.assertLessEqual(last[0] + last[2], 860.01)
        self.assertEqual(len({b[3] for b in shot["boxes"]}), 1)     # one height
        self.assertEqual(sum(1 for c in d.cells if 'edge="1"' in c), 2)

    def test_flow_column_stacks(self):
        d = Diagram("test")
        shot = kit.flow(d, ["one", "two"], vertical=True, node_w=300)
        self.assertLess(shot["boxes"][0][1], shot["boxes"][1][1])
        self.assertEqual(shot["bottom"], shot["boxes"][1][1] + shot["boxes"][1][3])

    def test_decision_tree_places_every_leaf_inside_the_frame(self):
        d = Diagram("test")
        tree = kit.T("root?", [("yes", kit.T("a?", [("", kit.T("leaf 1")), ("", kit.T("leaf 2"))])),
                               ("no", kit.T("leaf 3"))])
        shot = kit.decision_tree(d, tree)
        self.assertGreater(shot["bottom"], 100)
        d.save(Path(tempfile.gettempdir()) / "kit-tree-test.drawio")    # save() raises when content leaves the frame

    def test_plot_maps_values_onto_the_plot_area(self):
        d = Diagram("test")
        plot = kit.Plot(d, 0, 0, 860, 300, "t", y_ticks=[0, 100], x_ticks=[0, 10])
        self.assertAlmostEqual(plot.y_of(0), plot.py + plot.ph)
        self.assertAlmostEqual(plot.y_of(100), plot.py)
        self.assertAlmostEqual(plot.x_of(10) - plot.x_of(0), plot.pw)
        cat = kit.Plot(Diagram("c"), 0, 0, 860, 300, None, y_ticks=[0, 10], categories=["a", "b"])
        self.assertAlmostEqual(cat.x_of(0), cat.px + cat.pw / 4)

    def test_matrix_returns_a_cell_per_position(self):
        d = Diagram("test")
        shot = kit.matrix(d, ["X", "Y"], ["r1", "r2"], [["1", "2"], ["3", "4"]], colors={(0, 1): "teal"})
        self.assertEqual(set(shot["ids"]), {(0, 0), (0, 1), (1, 0), (1, 1)})
        self.assertLessEqual(shot["right"], 860.01)

    def test_compact(self):
        self.assertEqual(kit.compact(2_500_000), "2.5M")
        self.assertEqual(kit.compact(12_345), "12K")
        self.assertEqual(kit.compact(200), "200")


class AltTextTests(unittest.TestCase):
    def test_mock_alt_text(self):
        self.assertEqual(guides.alt_text({"kind": "excel-mock", "purpose": "The sheet after Step 4."}),
                         "A mock of the sheet after Step 4.")
        self.assertEqual(guides.alt_text({"kind": "pbi-mock", "purpose": "Model view with a dashed line."}),
                         "A mock of Model view with a dashed line.")
        self.assertEqual(guides.alt_text({"kind": "diagram", "purpose": "The path [of] a sale."}), "The path (of) a sale.")


if __name__ == "__main__":
    unittest.main()
