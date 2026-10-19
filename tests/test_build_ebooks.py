"""scripts/build_ebooks.py: the order of its steps and its exit status, with Quarto and the renderer replaced."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_ebooks, ebook_validate, figure_raster  # noqa: E402


def result(stem: str = "fig-01-a") -> figure_raster.Result:
    entry = {"mode": "palette", "bytes": 1000, "svg_bytes": 9000, "raw_bytes": 4000, "max_error": 5.0}
    return figure_raster.Result(stem, "cached", Path(stem + ".png"), entry)


class BuildEbooksTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="ebooks ")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.events: list[tuple] = []

        def render(root, quarto, fmt, destination, *, svg=False):
            self.events.append(("render", fmt, svg))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"x")
            return destination

        def ensure(root, stems=None, *, force=False, log=None, **kwargs):
            self.events.append(("figures", force))
            return [result()]

        for target, replacement in (("build_ebooks.render", render), ("figure_raster.ensure", ensure)):
            patcher = patch(f"scripts.{target}", replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def reports(self, epub_errors=(), docx_errors=()):
        def epub(path, **kwargs):
            report = ebook_validate.Report("epub", str(path))
            report.errors.extend(epub_errors)
            self.events.append(("validate", "epub", kwargs.get("expect_figures")))
            return report

        def docx(path, **kwargs):
            report = ebook_validate.Report("docx", str(path))
            report.errors.extend(docx_errors)
            self.events.append(("validate", "docx", kwargs.get("expect_figures")))
            return report

        for target, replacement in (("validate_epub", epub), ("validate_docx", docx),
                                    ("run_epubcheck", lambda path, report: None)):
            patcher = patch.object(ebook_validate, target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_figures_come_first_then_each_format_then_the_checks(self) -> None:
        self.reports()
        with patch("builtins.print"):
            status = build_ebooks.build(self.root, ["epub", "docx"], quarto="quarto")
        self.assertEqual(status, 0)
        self.assertEqual(self.events, [("figures", False), ("render", "epub", False), ("render", "docx", False),
                                       ("validate", "epub", 1), ("validate", "docx", 1)])
        for ext in ("epub", "docx"):
            self.assertTrue((self.root / "outputs" / "build" / "downloads" / f"book-latest.{ext}").is_file())
        report = json.loads((self.root / "outputs" / "build" / "ebook-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["figures"]["figures"], 1)
        self.assertEqual([r["kind"] for r in report["reports"]], ["epub", "docx"])

    def test_one_format_and_forced_figures(self) -> None:
        self.reports()
        with patch("builtins.print"):
            build_ebooks.build(self.root, ["docx"], force_figures=True, quarto="quarto")
        self.assertEqual(self.events[0], ("figures", True))
        self.assertEqual([e for e in self.events if e[0] == "render"], [("render", "docx", False)])

    def test_a_baseline_is_built_with_svg_before_the_optimized_file_and_compared(self) -> None:
        self.reports()
        compared: list[str] = []
        for name in ("compare_epub", "compare_docx"):
            patcher = patch.object(ebook_validate, name, lambda old, new, _n=name: (
                compared.append(_n), ebook_validate.Report(_n.replace("_", "-"), str(new)))[1])
            patcher.start()
            self.addCleanup(patcher.stop)
        with patch("builtins.print"):
            build_ebooks.build(self.root, ["epub"], baseline=True, quarto="quarto")
        self.assertEqual([e for e in self.events if e[0] == "render"], [("render", "epub", True), ("render", "epub", False)])
        self.assertEqual(compared, ["compare_epub"])
        self.assertTrue((self.root / "outputs" / "ebook-baseline" / "book-latest.epub").is_file())

    def test_a_failed_check_makes_the_exit_status_one(self) -> None:
        self.reports(docx_errors=["1 picture(s) are stretched"])
        with patch("builtins.print"):
            self.assertEqual(build_ebooks.build(self.root, ["epub", "docx"], quarto="quarto"), 1)

    def test_no_validate_only_builds(self) -> None:
        with patch("builtins.print"):
            self.assertEqual(build_ebooks.build(self.root, ["epub"], validate=False, quarto="quarto"), 0)
        self.assertNotIn("validate", [e[0] for e in self.events])

    def test_a_figure_error_stops_before_any_render(self) -> None:
        with patch("scripts.figure_raster.ensure", side_effect=figure_raster.RasterError("fig-01-a: Draw.io failed")):
            with patch("builtins.print"), patch("sys.stderr"):
                status = build_ebooks.main(["--epub", "--no-validate"])
        self.assertEqual(status, 1)
        self.assertEqual([e for e in self.events if e[0] == "render"], [])

    def test_command_line_selects_formats(self) -> None:
        with patch.object(build_ebooks, "build", return_value=0) as build:
            build_ebooks.main(["--epub"])
            self.assertEqual(build.call_args.args[1], ["epub"])
            build_ebooks.main([])
            self.assertEqual(build.call_args.args[1], ["epub", "docx"])
            build_ebooks.main(["--docx", "--force-figures", "--baseline"])
            self.assertEqual(build.call_args.args[1], ["docx"])
            self.assertTrue(build.call_args.kwargs["force_figures"])
            self.assertTrue(build.call_args.kwargs["baseline"])


if __name__ == "__main__":
    unittest.main()
