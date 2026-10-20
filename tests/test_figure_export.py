"""The Draw.io figure exporter: export-once on CI, checksum freshness, lossless PNG compression."""
from __future__ import annotations

import base64
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import export_drawio_svgs


def write(root: Path, rel: str, text: str = "fixture") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


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
                              side_effect=lambda exe, src, out, padding, labels: write(root, str(out), '<svg/>')) as svg, \
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
                self.assertEqual('text-fallback', svg.call_args.args[-1])
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
        self.settings = {'padding': 0.5, 'labels': 'text-fallback'}
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
        self.assertFalse(self.state.current(self.source, self.svg, {'padding': 2, 'labels': 'text-fallback'}))
        self.assertFalse(self.state.current(self.source, self.svg, {'padding': 0.5, 'labels': 'png-fallback'}))
        self.assertFalse(self.state.current(self.source, self.svg, {'padding': 0.5}), 'an entry made before the label mode existed')
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
            self.assertFalse(state.current(self.source, self.svg, {'padding': 2, 'labels': 'text-fallback'}))
            self.assertFalse(state.current(self.source, self.svg, {'padding': 0.5, 'labels': 'png-fallback'}))
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


class SvgLabelModeTests(unittest.TestCase):
    """What Draw.io is asked for and what is kept: a plain-text fallback (small) or a PNG of every label (large)."""

    EXPORT = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
              '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
              '<svg xmlns="http://www.w3.org/2000/svg" style="background: transparent; background-color: transparent; '
              'color-scheme: light;" version="1.1" width="100px" height="40px" viewBox="0 0 100 40"><defs/><g>'
              '<rect x="0" y="0" width="9" height="9" fill="#ffffff" stroke="#d5d8dc" pointer-events="all" '
              'style="fill: light-dark(rgb(255, 255, 255), rgb(18, 18, 18)); stroke: rgb(213, 216, 220);"/>'
              '<switch><foreignObject requiredFeatures="x"><div xmlns="http://www.w3.org/1999/xhtml">Hi</div></foreignObject>'
              '<text x="1" y="2">Hi</text></switch></g></svg>')

    def export(self, labels: str | None = None):
        commands = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = write(root, 'src/figure.drawio', '<mxfile><diagram/></mxfile>')
            output = root / 'svg' / 'figure.svg'

            def fake(command, src, target, kind):
                commands.append(command)
                target.write_text(self.EXPORT, encoding='utf-8')

            with patch.object(export_drawio_svgs, 'run_drawio', side_effect=fake), \
                 patch.object(export_drawio_svgs, 'optimize_svg') as optimize:
                arguments = (Path('drawio'), source, output, 0.5) + ((labels,) if labels else ())
                export_drawio_svgs.export_svg(*arguments)
            return commands[0], output.read_text(encoding='utf-8'), optimize

    def test_the_default_asks_draw_io_not_to_draw_a_png_of_every_label(self) -> None:
        command, _, optimize = self.export()
        self.assertEqual(['--embed-svg-fonts', 'false'], command[command.index('--embed-svg-fonts'):][:2])
        optimize.assert_not_called()

    def test_png_fallback_is_draw_ios_own_export_with_its_pngs_recompressed(self) -> None:
        command, _, optimize = self.export('png-fallback')
        self.assertNotIn('--embed-svg-fonts', command)
        optimize.assert_called_once()

    def test_the_markup_no_viewer_needs_is_dropped_and_the_label_is_kept_in_both_modes(self) -> None:
        for labels in ('text-fallback', 'png-fallback'):
            _, text, _ = self.export(labels)
            self.assertNotIn('<defs/>', text)
            self.assertNotIn('DOCTYPE', text)
            self.assertNotIn('pointer-events', text)
            self.assertNotIn('light-dark(', text)
            self.assertIn('<rect x="0" y="0" width="9" height="9" fill="#ffffff" stroke="#d5d8dc"/>', text)
            self.assertIn('<div xmlns="http://www.w3.org/1999/xhtml">Hi</div>', text)
            self.assertIn('<text x="1" y="2">Hi</text>', text)
            self.assertIn('background-color: #FFFFFF;', text)
            self.assertIn('viewBox="-0.5 -0.5 101 41"', text)

    def test_an_unknown_mode_is_refused(self) -> None:
        with self.assertRaises(export_drawio_svgs.ExportError):
            self.export('raster')

    def test_the_default_mode_is_the_small_one(self) -> None:
        self.assertEqual('text-fallback', export_drawio_svgs.DEFAULT_SVG_LABELS)
        self.assertEqual(('text-fallback', 'png-fallback'), export_drawio_svgs.SVG_LABELS)


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


class SlidePngTests(unittest.TestCase):
    def test_png_export_scales_with_a_border_and_checks_the_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = write(root, 'figure.drawio', '<mxfile><diagram/></mxfile>')
            output = root / 'out/figure.png'
            png = (b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR'
                   + struct.pack('>IIBBBBB', 4, 2, 8, 2, 0, 0, 0) + b'\0\0\0\0')

            def fake(command, src, temp_output, kind):
                self.assertEqual(['--scale', '2', '--border', '8'], command[4:8])
                temp_output.write_bytes(png)
            with patch.object(export_drawio_svgs, 'run_drawio', side_effect=fake):
                export_drawio_svgs.export_png(Path('drawio'), source, output)
            self.assertTrue(output.read_bytes().startswith(b'\x89PNG'))


if __name__ == "__main__":
    unittest.main()
