"""Build coordination tests use fake renderers; no Quarto or dataset is needed."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import build_all


def write(root: Path, rel: str, text: str = "fixture") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def manifest() -> dict:
    return {"version": 1, "toolchain": {"quarto": "1.9.36"}, "chapters": [
        {"id": "chapter-01", "source": "chapter-01/index.qmd", "status": "approved"},
        {"id": "chapter-02", "source": "chapter-02/index.qmd", "status": "pilot"},
        {"id": "chapter-03", "source": "chapter-03/index.qmd", "status": "deferred"},
    ], "public_assets": [], "public_fragments": []}


def stage_products(root: Path) -> None:
    for ext in ("pdf", "epub", "docx"):
        write(root, f"outputs/build/downloads/book-latest.{ext}", ext)
    for number in (1, 2):
        chapter = f"chapter-{number:02}"
        write(root, f"slides/_build/revealjs/{chapter}/index.html", f"<html>{chapter}</html>")
        write(root, f"slides/_build/pptx/{chapter}/{chapter}.pptx", chapter)
    write(root, "slides/_build/revealjs/site_libs/revealjs/plugin/notes/speaker-view.html", "notes runtime")
    write(root, "slides/_build/revealjs/_shared/generated/chart.svg", "<svg/>")


class BuildCoordinationTests(unittest.TestCase):
    def test_downloads_survive_destructive_renders_and_final_html_is_last(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = manifest()
            calls = []
            def fake_render(workdir, command, env):
                self.assertEqual(root, workdir)
                fmt = command[command.index("--to") + 1]
                calls.append(fmt)
                self.assertEqual("0", env["AA_SLIDES_INCLUDE_PILOT"])
                if "slides" in command:
                    if fmt == "revealjs":
                        for chapter in ("chapter-01", "chapter-02"):
                            write(root, f"slides/_build/revealjs/{chapter}/index.html", "<html/>")
                        write(root, "slides/_build/revealjs/site_libs/notes.js", "notes()")
                    else:
                        for chapter in ("chapter-01", "chapter-02"):
                            write(root, f"slides/_build/pptx/{chapter}/{chapter}.pptx")
                    return
                if (root / "_book").exists():
                    shutil.rmtree(root / "_book")
                if fmt == "html":
                    write(root, "_book/index.html", "<html/>")
                else:
                    write(root, f"_book/Accounting-Analytics.{fmt}", fmt)
            with patch.object(build_all, "source_checks", return_value=[]), \
                 patch.object(build_all.subprocess, "check_output", return_value="1.9.36\n"), \
                 patch.object(build_all, "prepare"), \
                 patch.object(build_all, "verify_outputs", return_value=[]), \
                 patch.object(build_all, "run", side_effect=fake_render):
                build_all.build(root, data, "fake-quarto")
                self.assertEqual(["pdf", "epub", "docx", "revealjs", "pptx", "html"], calls)
                for ext in ("pdf", "epub", "docx"):
                    self.assertEqual(ext, (root / f"_book/downloads/book-latest.{ext}").read_text())
                self.assertFalse((root / "_book/slides/chapter-02").exists())
                self.assertTrue((root / "_book/slides/site_libs/notes.js").is_file())
                calls.clear()
                build_all.build(root, data, "fake-quarto")
                self.assertEqual("html", calls[-1])
                self.assertTrue((root / "_book/slides/chapter-01/chapter-01.pptx").is_file())

    def test_slides_only_skips_book_and_retains_pilot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(build_all, "source_checks", return_value=[]), \
                 patch.object(build_all.subprocess, "check_output", return_value="1.9.36"), \
                 patch.object(build_all, "prepare"), \
                 patch.object(build_all, "verify_outputs", return_value=[]) as verify, \
                 patch.object(build_all, "run") as run, \
                 patch.object(build_all, "assemble") as assemble:
                build_all.build(root, manifest(), "fake-quarto", slides_only=True)
            self.assertEqual(2, run.call_count)
            self.assertEqual(1, verify.call_count)
            assemble.assert_not_called()
            report = json.loads((root / "outputs/build/build-report.json").read_text())
            self.assertTrue(report["includes_pilot"])
            self.assertEqual("not-run", report["powerpoint_review"])

    def test_version_mismatch_stops_before_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(build_all, "source_checks", return_value=[]), \
                 patch.object(build_all.subprocess, "check_output", return_value="1.8.0"), \
                 patch.object(build_all, "prepare") as prepare:
                with self.assertRaisesRegex(ValueError, "required"):
                    build_all.build(Path(temp), manifest(), "fake-quarto")
                prepare.assert_not_called()


class AssemblyTests(unittest.TestCase):
    def test_assembly_preserves_runtime_and_prunes_removed_and_pilot_decks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            write(root, "_book/slides/chapter-19/index.html", "stale published artifact")
            write(root, "slides/_build/revealjs/chapter-03/index.html", "stale removed deck")
            build_all.assemble(root, manifest())
            self.assertTrue((root / "_book/slides/site_libs/revealjs/plugin/notes/speaker-view.html").is_file())
            self.assertTrue((root / "_book/slides/_shared/generated/chart.svg").is_file())
            for chapter in ("chapter-02", "chapter-03", "chapter-19"):
                self.assertFalse((root / "_book/slides" / chapter).exists(), chapter)

    def test_review_assembly_keeps_pilot_without_mutating_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            data = manifest()
            original = copy.deepcopy(data)
            build_all.assemble(root, data, include_pilot=True)
            self.assertTrue((root / "_book/slides/chapter-02/chapter-02.pptx").is_file())
            self.assertEqual(original, data)

    def test_no_approved_decks_clears_previous_public_slide_subtree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            write(root, "_book/slides/chapter-01/index.html", "stale")
            data = manifest()
            data["chapters"][0]["status"] = "deferred"
            build_all.assemble(root, data)
            self.assertFalse((root / "_book/slides").exists())

    def test_source_files_in_rendered_tree_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            write(root, "slides/_build/revealjs/private.qmd", "raw authoring input")
            with self.assertRaisesRegex(ValueError, "Unexpected source"):
                build_all.assemble(root, manifest())

    def test_recursive_build_resources_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, '_book/index.html', '<html/>')
            write(root, 'slides/_build/revealjs/_build/pptx/_shared/chart.svg', '<svg/>')
            with self.assertRaisesRegex(ValueError, 'Nested build directory'):
                build_all.assemble(root, manifest())

    def test_known_reveal_runtime_descriptor_is_packaged_but_arbitrary_yaml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            relative = "chapter-01/index_files/libs/revealjs/plugin/pdf-export/plugin.yml"
            descriptor = write(root, "slides/_build/revealjs/" + relative, "name: PdfExport\nscript: pdfexport.js\n")
            write(root, "slides/_build/revealjs/" + relative.replace("plugin.yml", "pdfexport.js"), "vendor runtime")
            plugins = {
                "quarto-line-highlight": ("# adapted from https://github.com/hakimel/reveal.js/tree/master/plugin/highlight\n"
                    "name: QuartoLineHighlight\nscript: line-highlight.js\nstylesheet: line-highlight.css\n",
                    ["line-highlight.js", "line-highlight.css"]),
                "quarto-support": ("name: QuartoSupport\nscript: support.js\nstylesheet: footer.css\nconfig:\n  smaller: false\n",
                    ["support.js", "footer.css"]),
                "reveal-menu": ('name: RevealMenu\nscript: [menu.js, quarto-menu.js]\nstylesheet: [menu.css, quarto-menu.css]\n'
                    'config:\n  menu:\n    side: "left"\n    useTextContentForMissingTitles: true\n'
                    '    markers: false\n    loadIcons: false\n', ["menu.js", "quarto-menu.js", "menu.css", "quarto-menu.css"]),
            }
            for plugin, (content, resources) in plugins.items():
                folder = "slides/_build/revealjs/chapter-01/index_files/libs/revealjs/plugin/" + plugin
                write(root, folder + "/plugin.yml", content)
                for name in resources:
                    write(root, folder + "/" + name, "vendor runtime")
            build_all.assemble(root, manifest())
            self.assertTrue((root / "_book/slides" / relative).is_file())
            descriptor.write_text("name: PdfExport\nscript: pdfexport.js\nprivate: extra author content\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unexpected source"):
                build_all.assemble(root, manifest())
            descriptor.write_text("name: PdfExport\nscript: pdfexport.js\n", encoding="utf-8")
            write(root, "slides/_build/revealjs/chapter-01/other-plugin.yml", descriptor.read_text())
            with self.assertRaisesRegex(ValueError, "Unexpected source"):
                build_all.assemble(root, manifest())


class SourceAndPreviewTests(unittest.TestCase):
    def test_source_check_compares_manifest_to_explicit_render_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, "slides/_quarto.yml", json.dumps({"project": {"render": ["chapter-01/index.qmd"]}}))
            write(root, "slides/theme/reference-base.pptx")
            write(root, "slides/filters/images.lua")
            with patch.object(build_all, "verify_sources", return_value=[]), \
                 patch("scripts.slides.refresh.check_fresh", return_value=[]):
                self.assertTrue(any("render list" in error for error in build_all.source_checks(root, manifest())))
                write(root, "slides/_quarto.yml", json.dumps({"project": {"render": ["chapter-01/index.qmd", "chapter-02/index.qmd"]}}))
                self.assertEqual([], build_all.source_checks(root, manifest()))

    def test_preview_refreshes_shared_inputs_before_touching_deck(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = manifest()
            events = []
            process = Mock()
            process.wait.return_value = 0
            process.poll.return_value = 0
            stop = Mock()
            stop.wait.side_effect = [False, True]
            thread = Mock()
            def start_thread(*, target, daemon):
                thread.start.side_effect = target
                return thread
            with patch.object(build_all, "prepare", side_effect=lambda *args: events.append("prepare")), \
                 patch.object(build_all, "source_checks", return_value=[]) as checks, \
                 patch.object(build_all, "load_manifest", return_value=data), \
                 patch.object(build_all, "dependency_state", side_effect=[("old",), ("changed",), ("changed",)]), \
                 patch.object(build_all.subprocess, "Popen", return_value=process), \
                 patch.object(build_all.threading, "Event", return_value=stop), \
                 patch.object(build_all.threading, "Thread", side_effect=start_thread), \
                 patch.object(Path, "touch", side_effect=lambda: events.append("touch")):
                build_all.preview(root, data, "fake-quarto", "chapter-02")
            self.assertEqual(["prepare", "prepare", "touch"], events)
            checks.assert_called_once_with(root, data)
            process.terminate.assert_not_called()
            stop.set.assert_called_once()

    def test_preview_stops_when_changed_sources_need_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            process = Mock()
            process.wait.return_value = 0
            process.poll.return_value = 0
            stop = Mock()
            stop.wait.return_value = False
            thread = Mock()
            def start_thread(*, target, daemon):
                thread.start.side_effect = target
                return thread
            with patch.object(build_all, "prepare") as prepare, \
                 patch.object(build_all, "source_checks", return_value=["editorial review required"]), \
                 patch.object(build_all, "load_manifest", return_value=manifest()), \
                 patch.object(build_all, "dependency_state", side_effect=[("old",), ("changed",)]), \
                 patch.object(build_all.subprocess, "Popen", return_value=process), \
                 patch.object(build_all.threading, "Event", return_value=stop), \
                 patch.object(build_all.threading, "Thread", side_effect=start_thread):
                with self.assertRaisesRegex(RuntimeError, "editorial review"):
                    build_all.preview(root, manifest(), "fake-quarto", "chapter-01")
            prepare.assert_called_once()
            process.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
