"""The print covers (scripts/print/cover*.py): the ISBN barcode's encoding and decoder, the IDML template
reader against IngramSpark's templates (skipped when drafts/cover-print-template is absent), the artwork's
mirrored wrap and ink limit, the Draw.io export's recoloring, and the words on the cover. The PDF tests need
PyMuPDF and are skipped without it."""
from __future__ import annotations

import importlib.util
import io
import re
import sys
import unittest
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.print import cover_art  # noqa: E402
from scripts.print.cover_barcode import decode_ean13, decode_scanline, ean13_modules  # noqa: E402
from scripts.print.cover_template import find_templates, isbn13_valid, read_template  # noqa: E402

TEMPLATES = ROOT / 'drafts/cover-print-template'
HAS_FITZ = importlib.util.find_spec('fitz') is not None
CONFIG = yaml.safe_load((ROOT / '_quarto.yml').read_text(encoding='utf-8'))
ISBNS = {key: re.sub(r'\D', '', str(value)) for key, value in CONFIG['isbn'].items()}


class BarcodeTest(unittest.TestCase):
    def test_book_isbns_are_valid_and_round_trip(self):
        for key, isbn in ISBNS.items():
            self.assertTrue(isbn13_valid(isbn), key)
            self.assertEqual(decode_ean13(ean13_modules(isbn)), isbn, key)

    def test_known_ean13(self):
        # The pattern of 9780306406157 from the EAN-13 specification: left guard, first digit 9's parity LGGLGL.
        modules = ean13_modules('9780306406157')
        self.assertEqual(len(modules), 95)
        self.assertEqual(modules[:3], '101')
        self.assertEqual(modules[45:50], '01010')

    def test_rejects_a_damaged_pattern(self):
        modules = list(ean13_modules(ISBNS['hardcover']))
        modules[10] = '1' if modules[10] == '0' else '0'
        self.assertNotEqual(decode_ean13(''.join(modules)), ISBNS['hardcover'])

    def test_decodes_a_scan_line_with_narrowed_bars(self):
        isbn = ISBNS['paperback-bw']
        pitch, narrower = 8, 2   # pixels per module; each bar drawn two pixels narrower than its modules
        row = [False] * 40
        for module in ean13_modules(isbn):
            row += ([True] * (pitch) if module == '1' else [False] * pitch)
        # narrow every bar: take the last `narrower` pixels of each dark run back to white
        out, run = [], 0
        for value in row:
            run = run + 1 if value else 0
            out.append(value)
        shrunk = []
        index = 0
        while index < len(out):
            if out[index]:
                end = index
                while end < len(out) and out[end]:
                    end += 1
                shrunk += [True] * (end - index - narrower) + [False] * narrower
                index = end
            else:
                shrunk.append(False)
                index += 1
        self.assertEqual(decode_scanline(shrunk + [False] * 40), isbn)


@unittest.skipUnless(TEMPLATES.is_dir() and find_templates(TEMPLATES), 'IngramSpark cover templates not present')
class TemplateTest(unittest.TestCase):
    def test_every_template_is_one_of_the_books_isbns(self):
        for path in find_templates(TEMPLATES):
            self.assertIn(read_template(path).isbn, ISBNS.values(), path.name)

    def test_zones_nest(self):
        for path in find_templates(TEMPLATES):
            t = read_template(path)
            self.assertLess(t.back.x1, t.spine.x1)
            self.assertAlmostEqual(t.back.x1 if t.kind == 'perfect' else t.spine.x0, t.spine.x0, delta=0.5)
            for face, safe in ((t.back, t.back_safe), (t.spine, t.spine_safe), (t.front, t.front_safe)):
                self.assertGreater(safe.x0, face.x0)
                self.assertLess(safe.x1, face.x1)
                self.assertGreater(safe.y0, face.y0)
                self.assertLess(safe.y1, face.y1)
            self.assertLessEqual(t.art.x0, t.back.x0)
            self.assertGreaterEqual(t.art.x1, t.front.x1)
            self.assertGreaterEqual(t.page.w, t.art.w)
            self.assertGreater(t.barcode.x0, t.back_safe.x0)
            self.assertLess(t.barcode.x1, t.back_safe.x1)
            self.assertLess(t.barcode.y1, t.back_safe.y1)

    def test_paperback_geometry(self):
        for path in find_templates(TEMPLATES):
            t = read_template(path)
            if t.kind != 'perfect':
                continue
            self.assertAlmostEqual(t.back.w / 72, 8.5, places=2)
            self.assertAlmostEqual(t.front.w / 72, 8.5, places=2)
            self.assertAlmostEqual(t.back.h / 72, 11.0, places=2)
            self.assertAlmostEqual(t.art.h / 72, 11.25, places=2)   # 0.125 in of bleed above and below
            self.assertAlmostEqual(t.page.w / 72, 21.0, places=2)
            self.assertAlmostEqual(t.page.h / 72, 12.0, places=2)


class ArtTest(unittest.TestCase):
    def test_reflect_mirrors_at_the_edges(self):
        index = np.array([-3, -1, 0, 4, 5, 6, 9])
        self.assertEqual(cover_art._reflect(index, 5).tolist(), [2, 0, 0, 4, 4, 3, 0])

    def test_left_of_the_edge_uses_only_the_strip(self):
        index = np.arange(-30, 0)
        self.assertLess(cover_art._left_columns(index, 100, 10).max(), 10)
        self.assertEqual(cover_art._left_columns(np.array([0, 50, 99]), 100, 10).tolist(), [0, 50, 99])

    def test_adobe_marker_is_stripped_and_the_image_survives(self):
        cmyk = np.zeros((16, 16, 4), dtype=np.uint8)
        cmyk[..., 0], cmyk[..., 3] = 200, 40
        jpeg = cover_art.cmyk_jpeg_bytes(cmyk, 95, 300)
        self.assertNotIn(b'\xff\xee', jpeg)
        decoded = cover_art.decode_cmyk_jpeg(jpeg)
        self.assertLessEqual(int(np.abs(decoded.astype(int) - cmyk.astype(int)).max()), 3)

    def test_ink_limit_holds_for_the_dark_ground(self):
        profile = next(iter(Path('C:/Program Files/gs').glob('gs*/iccprofiles/default_cmyk.icc')), None) \
            if sys.platform == 'win32' else None
        if profile is None:
            self.skipTest('Ghostscript CMYK profile not found')
        pixels = np.array([[[3, 9, 36], [255, 255, 255], [227, 169, 59], [0, 0, 0]]], dtype=np.uint8)
        cmyk = cover_art.to_cmyk(pixels, profile, 220.0)
        self.assertLessEqual(cover_art.max_total_ink(cmyk), 220.5)
        self.assertEqual(cmyk[0, 1].tolist(), [0, 0, 0, 0])      # paper white stays paper


@unittest.skipUnless(HAS_FITZ, 'PyMuPDF not installed')
class OverlayTest(unittest.TestCase):
    def test_white_page_background_is_removed(self):
        from scripts.print.cover import remove_page_background
        stream = (b'.24 0 0 -.24 0 778 cm\nq\n0 0 5426 3240 re\nW* n\nq\n3 0 0 3 0 0 cm\n1 1 1 RG 1 1 1 rg\n/G3 gs\n'
                  b'0 0 1737 1037 re\nf\nQ\nQ\nq\n1 0 0 -1 10 20 cm\nBT /F1 12 Tf (x) Tj ET\nQ\n')
        out = remove_page_background(stream)
        self.assertNotIn(b're', out.replace(b'Tf', b'').replace(b'Tj', b''))
        self.assertIn(b'BT', out)

    def test_a_block_that_is_not_the_background_stops_the_build(self):
        from scripts.print.cover import remove_page_background
        with self.assertRaises(ValueError):
            remove_page_background(b'q\n1 0 0 rg\n0 0 10 10 re\nf\nQ\n')


class CopyTest(unittest.TestCase):
    copy = yaml.safe_load((ROOT / 'print/cover/cover.yml').read_text(encoding='utf-8'))

    def test_front_matches_the_title_page(self):
        pages = (ROOT / 'front-matter/_book-pages.qmd').read_text(encoding='utf-8')
        for key in ('author', 'publisher'):
            self.assertIn(self.copy['front'][key], pages)
        self.assertIn(' '.join(self.copy['front']['title']).title(), CONFIG['book']['title'])
        self.assertEqual(self.copy['front']['subtitle'].title(), CONFIG['book']['title'].split(': ')[1])

    def test_back_cover_has_no_counts_that_age(self):
        text = yaml.dump(self.copy['back'])
        self.assertIsNone(re.search(r'\b\d+\s+(chapters|tables|exercises|cases|tutorials|parts)\b', text, re.I))

    def test_back_cover_names_the_site_and_the_license(self):
        footer = ' '.join(self.copy['back']['footer'])
        self.assertIn('aa.accountinganalyticshub.com', footer)
        self.assertIn('CC BY-SA 4.0', footer)


if __name__ == '__main__':
    unittest.main()
