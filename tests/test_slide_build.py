"""Build coordination tests use fake renderers; no Quarto or dataset is needed."""
from __future__ import annotations

import copy
import base64
import json
import os
import shutil
import sys
import subprocess
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import build_all, export_drawio_svgs


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
                if 'scripts/export_drawio_svgs.py' in command:
                    self.assertNotIn('AA_DRAWIO_EXPORTS_READY', env)
                    calls.append('figures')
                    return
                self.assertEqual('1', env['AA_DRAWIO_EXPORTS_READY'])
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
                self.assertEqual(["figures", "pdf", "epub", "docx", "revealjs", "pptx", "html"], calls)
                for ext in ("pdf", "epub", "docx"):
                    self.assertEqual(ext, (root / f"_book/downloads/book-latest.{ext}").read_text())
                self.assertFalse((root / "_book/slides/chapter-02").exists())
                self.assertTrue((root / "_book/slides/site_libs/notes.js").is_file())
                calls.clear()
                build_all.build(root, data, "fake-quarto")
                self.assertEqual(1, calls.count('figures'))
                self.assertEqual('figures', calls[0])
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

    def test_export_failure_stops_before_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(build_all, 'source_checks', return_value=[]), \
                 patch.object(build_all.subprocess, 'check_output', return_value='1.9.36'), \
                 patch.object(build_all, 'prepare'), \
                 patch.object(build_all, 'run', side_effect=subprocess.CalledProcessError(1, 'export')) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    build_all.build(Path(temp), manifest(), 'fake-quarto')
            self.assertEqual(1, run.call_count)
            self.assertIn('scripts/export_drawio_svgs.py', run.call_args.args[1])


class FigureExportHookTests(unittest.TestCase):
    def test_ci_exports_once_then_reuses_for_each_book_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            diagram = '<mxfile><diagram/></mxfile>'
            write(root, 'src/figure.drawio', diagram)
            write(root, 'cover.drawio', diagram)
            args = ['export_drawio_svgs.py', '--src-dir', str(root / 'src'),
                    '--manifest', str(root / 'export-manifest.json'),
                    '--out-dir', str(root / 'svg'), '--pdf-dir', str(root / 'pdf'),
                    '--cover-source', str(root / 'cover.drawio'),
                    '--cover-output', str(root / 'cover.png')]
            with patch.object(export_drawio_svgs, 'REPO_ROOT', root), \
                 patch.object(export_drawio_svgs, 'find_drawio_executable', return_value=Path('drawio')), \
                 patch.object(export_drawio_svgs, 'export_svg',
                              side_effect=lambda exe, src, out, padding: write(root, str(out), '<svg/>')) as svg, \
                 patch.object(export_drawio_svgs, 'export_pdf',
                              side_effect=lambda exe, src, out, **kwargs: write(root, str(out), 'PDF')) as pdf, \
                 patch.object(export_drawio_svgs, 'export_cover_png',
                              side_effect=lambda exe, src, out, w, h: write(root, str(out), 'PNG')) as cover, \
                 patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'AA_DRAWIO_EXPORTS_READY': '0'}):
                with patch.object(sys, 'argv', args):
                    self.assertEqual(0, export_drawio_svgs.run())
                os.environ['AA_DRAWIO_EXPORTS_READY'] = '1'
                for _ in ('pdf', 'epub', 'docx', 'html'):
                    with patch.object(sys, 'argv', args + ['--pre-render']):
                        self.assertEqual(0, export_drawio_svgs.run())
                self.assertEqual(1, svg.call_count)
                self.assertEqual(2, pdf.call_count)
                self.assertEqual(2, cover.call_count)
                self.assertEqual({'crop': False}, pdf.call_args.kwargs)
                self.assertEqual((510, 660), cover.call_args.args[-2:])
                # Normal explicit exports reuse the manifest; --force overrides it.
                for flags in ([], ['--pre-render', '--force']):
                    with patch.object(sys, 'argv', args + flags):
                        self.assertEqual(0, export_drawio_svgs.run())
                # A standalone Quarto render also reuses current outputs on CI.
                del os.environ['AA_DRAWIO_EXPORTS_READY']
                with patch.object(sys, 'argv', args + ['--pre-render']):
                    self.assertEqual(0, export_drawio_svgs.run())
                self.assertEqual(2, svg.call_count)
                self.assertEqual(4, pdf.call_count)
                self.assertEqual(4, cover.call_count)

    def test_skip_pdf_keeps_both_png_cover_sizes(self) -> None:
        outputs = export_drawio_svgs.cover_targets(Path('cover.png'), 2550, 3300, skip_pdf=True)
        self.assertEqual([(Path('cover.png'), {'width': 2550, 'height': 3300}),
                          (Path('cover-web.png'), {'width': 510, 'height': 660})], outputs)


class ExportFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(export_drawio_svgs, 'REPO_ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.source = write(self.root, 'src/figure.drawio', '<mxfile>\n<diagram/>\n</mxfile>\n')
        self.svg = write(self.root, 'svg/figure.svg', '<svg>\n<text>Label</text>\n</svg>\n')
        self.pdf = write(self.root, 'pdf/figure.pdf', 'PDF')
        self.path = self.root / 'export-manifest.json'
        self.state = export_drawio_svgs.ExportManifest(self.path)
        self.settings = {'padding': 0.5}
        self.state.remember(self.source, self.svg, self.settings)
        self.state.remember(self.source, self.pdf, {})
        self.state.save()

    def test_fresh_checkout_ignores_mtimes_and_normalizes_git_line_endings(self) -> None:
        # Simulate a fresh checkout where the source was written after its output.
        self.source.write_bytes(self.source.read_bytes().replace(b'\r\n', b'\n'))
        self.svg.write_bytes(self.svg.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        os.utime(self.source, (2000, 2000))
        os.utime(self.svg, (1000, 1000))
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}):
            state = export_drawio_svgs.ExportManifest(self.path)
            self.assertTrue(state.current(self.source, self.svg, self.settings))
            self.assertTrue(state.current(self.source, self.pdf, {}))

    def test_source_edit_rebuilds_both_formats_even_with_newer_outputs(self) -> None:
        self.source.write_text('<mxfile><diagram name="changed"/></mxfile>', encoding='utf-8')
        os.utime(self.source, (1000, 1000))
        os.utime(self.svg, (2000, 2000))
        os.utime(self.pdf, (2000, 2000))
        self.assertFalse(self.state.current(self.source, self.svg, self.settings))
        self.assertFalse(self.state.current(self.source, self.pdf, {}))

    def test_only_missing_modified_or_reconfigured_output_is_stale(self) -> None:
        self.assertFalse(self.state.current(self.source, self.svg, {'padding': 2}))
        self.assertTrue(self.state.current(self.source, self.pdf, {}))
        self.svg.write_text('<svg>modified</svg>', encoding='utf-8')
        self.assertFalse(self.state.current(self.source, self.svg, self.settings))
        self.svg.write_bytes(b'')
        self.assertFalse(self.state.current(self.source, self.svg, self.settings))
        self.svg.unlink()
        self.assertFalse(self.state.current(self.source, self.svg, self.settings))
        self.assertTrue(self.state.current(self.source, self.pdf, {}))
        with patch.object(export_drawio_svgs, 'EXPORT_RECIPE_VERSION', 2):
            self.assertFalse(self.state.current(self.source, self.pdf, {}))

    def test_timestamp_bootstrap_is_local_only_and_requires_default_settings(self) -> None:
        state = export_drawio_svgs.ExportManifest(self.root / 'missing.json')
        os.utime(self.source, (1000, 1000))
        os.utime(self.svg, (2000, 2000))
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}):
            self.assertFalse(state.current(self.source, self.svg, self.settings))
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'false'}):
            self.assertTrue(state.current(self.source, self.svg, self.settings))
            self.assertFalse(state.current(self.source, self.svg, {'padding': 2}))
            os.utime(self.source, (3000, 3000))
            self.assertFalse(state.current(self.source, self.svg, self.settings))

    def test_ci_all_current_does_not_require_drawio_or_rewrite_manifest(self) -> None:
        stamp = self.path.stat().st_mtime_ns
        args = ['export_drawio_svgs.py', '--manifest', str(self.path),
                '--src-dir', str(self.source.parent), '--out-dir', str(self.svg.parent),
                '--pdf-dir', str(self.pdf.parent), '--skip-cover']
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'AA_DRAWIO_EXPORTS_READY': '0'}), \
             patch.object(sys, 'argv', args), \
             patch.object(export_drawio_svgs, 'find_drawio_executable', side_effect=AssertionError('unneeded')):
            self.assertEqual(0, export_drawio_svgs.run())
        self.assertEqual(stamp, self.path.stat().st_mtime_ns)


class SvgCompressionTests(unittest.TestCase):
    @staticmethod
    def chunk(kind: bytes, content: bytes) -> bytes:
        return (struct.pack('>I', len(content)) + kind + content
                + struct.pack('>I', zlib.crc32(kind + content)))

    def png(self) -> tuple[bytes, bytes, bytes]:
        # Valid grayscale PNG with two IDAT chunks and metadata on both sides.
        pixels = (b'\0' + bytes(range(128))) * 128
        packed = zlib.compress(pixels, level=0)
        header = (b'\x89PNG\r\n\x1a\n'
                  + self.chunk(b'IHDR', struct.pack('>IIBBBBB', 128, 128, 8, 0, 0, 0, 0))
                  + self.chunk(b'gAMA', struct.pack('>I', 45455)))
        trailer = self.chunk(b'tEXt', b'Title\0Label fallback') + self.chunk(b'IEND', b'')
        png = header + self.chunk(b'IDAT', packed[:50]) + self.chunk(b'IDAT', packed[50:]) + trailer
        return png, header, trailer

    def test_recompression_preserves_scanlines_metadata_and_checksums(self) -> None:
        original, header, trailer = self.png()
        optimized = export_drawio_svgs.compress_png_losslessly(original)
        self.assertLess(len(optimized), len(original))
        self.assertTrue(optimized.startswith(header))
        self.assertTrue(optimized.endswith(trailer))
        chunk = optimized[len(header):-len(trailer)]
        self.assertEqual(b'IDAT', chunk[4:8])
        self.assertEqual(len(chunk) - 12, struct.unpack('>I', chunk[:4])[0])
        self.assertEqual(zlib.crc32(chunk[4:-4]), struct.unpack('>I', chunk[-4:])[0])
        self.assertEqual((b'\0' + bytes(range(128))) * 128, zlib.decompress(chunk[8:-4]))
        self.assertEqual(optimized, export_drawio_svgs.compress_png_losslessly(optimized))

    def test_svg_markup_is_byte_identical_and_second_pass_does_not_write(self) -> None:
        original, _, _ = self.png()
        template = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
                    b'<text x="1.2345">Keep  spaces &amp; text</text>'
                    b'<image href="data:image/png;base64,%s"/></svg>')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'figure.svg'
            svg = template % base64.b64encode(original)
            path.write_bytes(svg)
            saved = export_drawio_svgs.optimize_svg(path)
            expected = template % base64.b64encode(export_drawio_svgs.compress_png_losslessly(original))
            self.assertEqual(expected, path.read_bytes())
            self.assertEqual(len(svg) - len(expected), saved)
            timestamp = path.stat().st_mtime_ns
            self.assertEqual(0, export_drawio_svgs.optimize_svg(path))
            self.assertEqual(timestamp, path.stat().st_mtime_ns)

    def test_invalid_and_animated_pngs_are_unchanged(self) -> None:
        original, header, trailer = self.png()
        animated = header + self.chunk(b'acTL', struct.pack('>II', 1, 0)) + original[len(header):]
        bad_stream = header + self.chunk(b'IDAT', b'not zlib') + trailer
        bad_crc = original[:-1] + bytes([original[-1] ^ 1])
        for data in (b'not a png', original[:30], bad_crc, bad_stream, animated):
            with self.subTest(size=len(data)):
                self.assertEqual(data, export_drawio_svgs.compress_png_losslessly(data))


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
