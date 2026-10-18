"""The print interiors (scripts/print): the print palette against the figure standard and IngramSpark's ink
limit, the LaTeX color values against the palette, the figure recoloring of PDF content streams, the
Quarto profiles, and the PDF/X definition. The preflight test needs PyMuPDF and is skipped without it."""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts/figures'))
from scripts.print import palette  # noqa: E402
from scripts.print.pdfops import operations  # noqa: E402
from scripts.print.recolor import recolor_stream  # noqa: E402
from scripts.print.pdfx import pdfx_definition  # noqa: E402

HAS_FITZ = importlib.util.find_spec('pymupdf') is not None
DARK_FILLS = ('BLUE', 'TEAL', 'CORAL', 'AMBER', 'GRAY')
TINTS = ('BLUE_TINT', 'TEAL_TINT', 'AMBER_TINT', 'CORAL_TINT', 'GRAY_TINT')


def by_name() -> dict[str, tuple[tuple[int, int, int, int], float]]:
    return {name: (cmyk, gray) for name, cmyk, gray in palette.FIGURE_COLORS.values()}


class PaletteTest(unittest.TestCase):
    def test_covers_the_figure_palette(self):
        import drawio
        self.assertEqual({color.upper() for color in drawio.PALETTE}, set(palette.FIGURE_COLORS))

    def test_total_ink_within_ingramspark_limit(self):
        for name, cmyk, _ in palette.FIGURE_COLORS.values():
            self.assertLessEqual(palette.total_ink(cmyk), palette.MAX_TOTAL_INK, name)
        for name, (cmyk, _) in palette.LATEX_COLORS.items():
            self.assertLessEqual(palette.total_ink(cmyk), palette.MAX_TOTAL_INK, name)

    def test_text_ink_is_black_only(self):
        colors = by_name()
        self.assertEqual(colors['INK'], ((0, 0, 0, 100), 0.0))
        self.assertEqual(palette.LATEX_COLORS['Ink'], ((0, 0, 0, 100), 0.0))

    def test_gray_levels_keep_text_readable_and_fills_apart(self):
        colors = by_name()
        for name in DARK_FILLS:
            self.assertGreaterEqual(palette.contrast(1.0, colors[name][1]), 4.5, f'white text on {name}')
        levels = sorted(colors[name][1] for name in DARK_FILLS)
        self.assertTrue(all(b - a >= 0.07 for a, b in zip(levels, levels[1:])), levels)
        for name in TINTS + ('HIGHLIGHT',):
            self.assertLessEqual(colors[name][1], 0.88, f'{name} must be at least 12% black')
            self.assertGreaterEqual(palette.contrast(0.0, colors[name][1]), 4.5, f'ink text on {name}')
        self.assertLess(colors['HIGHLIGHT'][1], min(colors[name][1] for name in TINTS))
        self.assertLessEqual(colors['RULE'][1], 0.6)


class LatexColorsTest(unittest.TestCase):
    def definitions(self, name: str, model: str) -> dict[str, list[float]]:
        text = (ROOT / 'print' / name).read_text(encoding='utf-8')
        return {color: [float(v) for v in values.split(',')]
                for color, values in re.findall(r'\\definecolor\{([\w-]+)\}\{' + model + r'\}\{([^}]*)\}', text)}

    def test_color_interior_matches_palette(self):
        defined = self.definitions('book-print-color.tex', 'cmyk')
        for name, (cmyk, _) in palette.LATEX_COLORS.items():
            self.assertEqual(defined.get(name), [value / 100 for value in cmyk], name)

    def test_gray_interior_matches_palette(self):
        defined = self.definitions('book-print-bw.tex', 'gray')
        for name, (_, gray) in palette.LATEX_COLORS.items():
            self.assertEqual(defined.get(name), [gray], name)
        self.assertEqual(defined.get('ObjectivesTint'), [palette.OBJECTIVES_TINT_GRAY])

    def test_named_objectives_background(self):
        text = (ROOT / 'styles/book-pdf.tex').read_text(encoding='utf-8')
        self.assertIn('colback=ObjectivesTint', text)


class OperationsTest(unittest.TestCase):
    def test_strings_arrays_and_dictionaries_are_operands(self):
        ops = list(operations(b'/P <</MCID 0>> BDC [(1 0 0 rg) -250 <0041>] TJ (a\\) b) Tj EMC'))
        self.assertEqual([op.operator for op in ops], ['BDC', 'TJ', 'Tj', 'EMC'])
        self.assertEqual(len(ops[1].operands), 1)

    def test_numbers(self):
        op = next(operations(b'.5 -1 2. rg'))
        self.assertEqual(op.numbers(), [0.5, -1.0, 2.0])


class RecolorTest(unittest.TestCase):
    STREAM = b'q .1725 .2431 .3137 rg 0 0 10 10 re f 0.102 0.3216 0.4627 RG (2 0 0 rg) Tj 1 1 1 rg Q'

    def test_cmyk(self):
        out, count = recolor_stream(self.STREAM, 'cmyk', 'test')
        self.assertEqual(count, 3)
        self.assertIn(b'0 0 0 1 k', out)
        self.assertIn(b'1 0.73 0.35 0.19 K', out)
        self.assertIn(b'0 0 0 0 k', out)
        self.assertIn(b'(2 0 0 rg) Tj', out)  # text is not a color
        self.assertNotIn(b' rg', out.replace(b'(2 0 0 rg)', b''))

    def test_gray(self):
        out, _ = recolor_stream(self.STREAM, 'gray', 'test')
        self.assertIn(b'0 g', out)
        self.assertIn(b'0.1 G', out)
        self.assertIn(b'1 g', out)

    def test_unknown_color_stops(self):
        with self.assertRaisesRegex(ValueError, 'not in the print palette'):
            recolor_stream(b'1 0 0 rg', 'cmyk', 'test')
        with self.assertRaisesRegex(ValueError, 'unexpected color operator'):
            recolor_stream(b'/CS0 cs 1 sc', 'gray', 'test')


class ProfilesTest(unittest.TestCase):
    def test_profiles(self):
        for variant, header in (('color', 'book-print-color.tex'), ('bw', 'book-print-bw.tex')):
            config = yaml.safe_load((ROOT / f'_quarto-print-{variant}.yml').read_text(encoding='utf-8'))
            self.assertIs(config['print'], True)
            self.assertEqual(config['project']['output-dir'], f'outputs/print/render/{variant}')
            pdf = config['format']['pdf']
            self.assertEqual(pdf['include-in-header'], ['print/book-print.tex', f'print/{header}'])
            self.assertIs(pdf['colorlinks'], False)
            for path in pdf['include-in-header']:
                self.assertTrue((ROOT / path).is_file(), path)

    def test_print_headers_stay_out_of_book_inputs(self):
        from scripts.release import BOOK_INPUTS
        self.assertNotIn('print', BOOK_INPUTS)

    def test_pdfx_definition(self):
        text = pdfx_definition('A (Title)', Path('C:/gs/iccprofiles/default_cmyk.icc'), 1)
        self.assertIn('/GTS_PDFXVersion (PDF/X-1a:2001)', text)
        self.assertIn(r'/Title (A \(Title\))', text)
        self.assertIn('(C:/gs/iccprofiles/default_cmyk.icc) (r) file', text)
        self.assertIn('/OutputIntents', text)


@unittest.skipUnless(HAS_FITZ, 'PyMuPDF is not installed')
class PreflightTest(unittest.TestCase):
    def test_flags_rgb_and_odd_pages(self):
        import pymupdf as fitz
        from scripts.print.preflight import check_color, check_pages
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'one.pdf'
            doc = fitz.open()
            page = doc.new_page(width=612, height=792)
            page.insert_text((72, 72), 'Accounting Analytics', color=(1, 0, 0))
            doc.save(path)
            doc.close()
            doc = fitz.open(path)
            try:
                self.assertFalse(check_pages(doc).ok)
                color, _ = check_color(doc, 'gray')
                self.assertFalse(color.ok)
            finally:
                doc.close()


if __name__ == '__main__':
    unittest.main()
