"""Smaller Draw.io SVGs: stripping redundant markup, reading labels, finding single-line labels, the converted copy."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import svg_lab, svg_native as sn

HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" '
        'width="200px" height="60px" viewBox="-0.5 -0.5 200 60">')


def html_label(cell: str, body: str, *, width: int = 100, size: int = 12, nowrap: bool = False, color: str = "#2C3E50",
               fallback: str = "", background: str = "", rotate: str = "") -> str:
    space = "nowrap" if nowrap else "normal"
    turn = f' transform="{rotate}"' if rotate else ""
    return (f'<g data-cell-id="{cell}"><g><g{turn}><switch><foreignObject style="overflow: visible; text-align: left;" '
            f'pointer-events="none" width="100%" height="100%" requiredFeatures="http://www.w3.org/TR/SVG11/feature#Extensibility">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" style="display: flex; align-items: unsafe center; justify-content: '
            f'unsafe flex-start; width: {width}px; height: 1px; padding-top: 12px; margin-left: 8px;">'
            f'<div style="box-sizing: border-box; font-size: 0; text-align: left; color: {color}; ">'
            f'<div style="display: inline-block; font-size: {size}px; font-family: Helvetica; color: {color}; line-height: 1.2; '
            f'pointer-events: all; {background}white-space: {space}; word-wrap: normal; ">{body}</div></div></div></foreignObject>'
            f'<text x="8" y="12" fill="{color}" font-family="Helvetica" font-size="{size}px">{fallback}</text></switch></g></g></g>')


def native_label(cell: str, body: str, color: str = "#2C3E50") -> str:
    return (f'<g data-cell-id="{cell}"><g><g fill="{color}" font-family="Helvetica" font-size="12px" '
            f'style="fill: rgb(44, 62, 80);"><text x="8" y="12">{body}</text></g></g></g>')


def document(*parts: str) -> str:
    return HEAD + '<rect x="-0.5" y="-0.5" width="200" height="60" fill="#FFFFFF"/><defs/><g><g data-cell-id="0"><g data-cell-id="1">' \
        + "".join(parts) + "</g></g></g></svg>"


class StripTests(unittest.TestCase):
    SHAPE = ('<g data-cell-id="c1"><g transform="translate(0.5,0.5)"><rect x="0" y="0" width="110" height="24" fill="#ffffff" '
             'stroke="#d5d8dc" pointer-events="all" style="fill: rgb(255, 255, 255); stroke: rgb(213, 216, 220);"/></g></g>')

    def test_a_style_that_repeats_fill_and_stroke_is_dropped_with_pointer_events(self) -> None:
        stripped = sn.strip_svg_metadata(document(self.SHAPE))
        self.assertIn('<rect x="0" y="0" width="110" height="24" fill="#ffffff" stroke="#d5d8dc"/>', stripped)
        self.assertNotIn("pointer-events", stripped)
        self.assertNotIn("<defs/>", stripped)
        self.assertNotIn("DOCTYPE", stripped)
        self.assertIn('data-cell-id="c1"', stripped, "cell ids are kept unless asked")

    def test_a_style_that_differs_from_its_attribute_is_kept(self) -> None:
        shape = '<rect x="0" y="0" width="9" height="9" fill="#ffffff" stroke="#d5d8dc" style="fill: rgb(1, 2, 3);"/>'
        self.assertIn('style="fill: rgb(1, 2, 3);"', sn.strip_svg_metadata(document(shape)))

    def test_a_declaration_without_an_attribute_keeps_the_style(self) -> None:
        shape = '<path d="M 0 0 L 9 9" fill="none" style="stroke: rgb(44, 62, 80);"/>'
        self.assertIn("style=", sn.strip_svg_metadata(document(shape)))

    def test_hex_and_rgb_spellings_of_one_color_agree(self) -> None:
        self.assertEqual(sn.normalize_color("rgb(93, 109, 126)"), "#5d6d7e")
        self.assertEqual(sn.normalize_color("#5D6D7E"), "#5d6d7e")
        self.assertEqual(sn.normalize_color("#abc"), "#aabbcc")
        self.assertEqual(sn.normalize_color("light-dark(rgb(1, 2, 3), rgb(9, 9, 9))"), "#010203")
        self.assertEqual(sn.normalize_color("none"), "none")

    def test_cell_ids_go_only_when_asked_and_the_text_is_never_touched(self) -> None:
        label = html_label("c2", "Customer&gt;Order", fallback="Customer...")
        text = document(self.SHAPE, label)
        stripped = sn.strip_svg_metadata(text, sn.StripOptions(cell_ids=True))
        self.assertNotIn("data-cell-id", stripped)
        self.assertIn("Customer&gt;Order", stripped)
        self.assertIn("Customer...", stripped)

    def test_stripping_is_idempotent_and_leaves_other_tags_alone(self) -> None:
        text = document(self.SHAPE, html_label("c2", "x"), '<linearGradient id="g"/><polyline points="0,0 1,1" pointer-events="none"/>')
        once = sn.strip_svg_metadata(text)
        self.assertEqual(sn.strip_svg_metadata(once), once)
        self.assertIn("<linearGradient", once)
        self.assertIn('<polyline points="0,0 1,1"/>', once)

    def test_a_tag_written_differently_from_draw_io_is_left_alone(self) -> None:
        odd = '<rect  x="0" fill="#fff" pointer-events="all"  />'
        self.assertIn(odd, sn.strip_svg_metadata(document(odd)))

    def test_the_stripped_svg_is_well_formed(self) -> None:
        import xml.etree.ElementTree as ET
        ET.fromstring(sn.strip_svg_metadata(document(self.SHAPE, html_label("c2", "x"))))


class LabelTests(unittest.TestCase):
    def test_an_html_label_is_read_as_styled_runs(self) -> None:
        body = '<b>Audit</b> sql <font color="#5D6D7E" style="color: rgb(93, 109, 126);">gray</font><i>it</i>'
        [label] = sn.labels(document(html_label("c2", body, width=120, fallback="Audit sql...")))
        self.assertEqual((label.cell, label.kind, label.width, label.size, label.has_br), ("c2", "html", 120.0, 12.0, False))
        self.assertEqual(label.text, "Audit sql grayit")
        self.assertEqual(label.fallback, "Audit sql...")
        flags = {(run.text.strip(), run.bold, run.italic, run.color) for run in label.runs if run.text.strip()}
        self.assertEqual(flags, {("Audit", True, False, "#2c3e50"), ("sql", False, False, "#2c3e50"),
                                 ("gray", False, False, "#5d6d7e"), ("it", False, True, "#2c3e50")})

    def test_html_and_native_versions_of_a_label_have_the_same_signature(self) -> None:
        html_form = sn.labels(document(html_label("c2", "<b>Audit</b> sql&#160;&#160;x")))[0]
        native = sn.labels(document(
            native_label("c2", '<tspan font-weight="bold"><tspan>Audit</tspan></tspan><tspan> sql&#160;&#160;x</tspan>')))[0]
        self.assertEqual((html_form.kind, native.kind), ("html", "native"))
        self.assertEqual(html_form.text, native.text)
        self.assertEqual(html_form.signature(), native.signature())

    def test_a_different_color_or_weight_changes_the_signature(self) -> None:
        plain = sn.labels(document(native_label("c2", "<tspan>Audit</tspan>")))[0]
        bold = sn.labels(document(native_label("c2", '<tspan font-weight="bold">Audit</tspan>')))[0]
        gray = sn.labels(document(native_label("c2", '<tspan fill="#5D6D7E">Audit</tspan>')))[0]
        self.assertEqual(plain.text, bold.text)
        self.assertNotEqual(plain.signature(), bold.signature())
        self.assertNotEqual(plain.signature(), gray.signature())

    def test_a_br_is_noticed_and_the_png_fallback_box_is_read(self) -> None:
        text = document(html_label("c2", "one<br />two").replace(
            '<text x="8" y="12" fill="#2C3E50" font-family="Helvetica" font-size="12px"></text>',
            '<image x="8" y="5.5" width="96" height="31" xlink:href="data:image/png;base64,AAAA"/>'))
        [label] = sn.labels(text)
        self.assertTrue(label.has_br)
        self.assertEqual(label.image_box, (8.0, 5.5, 96.0, 31.0))

    def test_labels_are_attributed_to_the_innermost_cell(self) -> None:
        found = sn.labels(document(html_label("a", "one"), native_label("b", "<tspan>two</tspan>")))
        self.assertEqual([(label.cell, label.text) for label in found], [("a", "one"), ("b", "two")])


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.meter = sn.TextMeter()
        except (sn.FontMissing, ImportError) as exc:  # no Arial-like font here, or no Pillow (CI)
            raise unittest.SkipTest(str(exc))

    def label(self, body: str, **kwargs) -> sn.Label:
        return sn.labels(document(html_label("c2", body, **kwargs)))[0]

    def test_a_short_label_fits_and_a_long_one_wraps(self) -> None:
        self.assertTrue(sn.fits_on_one_line(self.label("Customer", width=96), self.meter))
        self.assertFalse(sn.fits_on_one_line(
            self.label("A long label that must wrap across several lines", width=96), self.meter))

    def test_a_br_always_means_more_than_one_line(self) -> None:
        self.assertFalse(sn.fits_on_one_line(self.label("a<br />b", width=400), self.meter))

    def test_nowrap_is_one_line_however_wide(self) -> None:
        self.assertTrue(sn.fits_on_one_line(self.label("a long label that does not wrap " * 4, width=50, nowrap=True), self.meter))

    def test_bold_text_is_measured_wider_than_regular(self) -> None:
        plain, bold = self.label("ShipmentDate", width=200), self.label("<b>ShipmentDate</b>", width=200)
        self.assertGreater(self.meter.width(bold.runs, bold.size), self.meter.width(plain.runs, plain.size))

    def test_the_margin_keeps_a_label_that_nearly_fills_its_box_in_html(self) -> None:
        text = self.label("ShipmentNumber", width=100)
        width = self.meter.width(text.runs, text.size)
        self.assertTrue(sn.fits_on_one_line(self.label("ShipmentNumber", width=int(width) + 5), self.meter))
        self.assertFalse(sn.fits_on_one_line(self.label("ShipmentNumber", width=int(width) + 1), self.meter))

    def test_a_symbol_arial_lacks_is_measured_as_a_full_em(self) -> None:
        symbol = self.label("▾", size=12)
        self.assertAlmostEqual(self.meter.width(symbol.runs, symbol.size), 12.0, places=3)

    def test_a_label_with_a_background_or_a_rotation_stays_html(self) -> None:
        plain = sn.labels(document(html_label("c2", "SalesOrderID = 1697", width=1, nowrap=True)))[0]
        backed = sn.labels(document(html_label("c2", "SalesOrderID = 1697", width=1, nowrap=True,
                                               background="background-color: #FFFFFF; ")))[0]
        turned = sn.labels(document(html_label("c2", "Sum", width=188, rotate="rotate(-90 15 727)")))[0]
        self.assertFalse(plain.background or plain.rotated)
        self.assertTrue(sn.fits_on_one_line(plain, self.meter))
        self.assertTrue(backed.background)
        self.assertFalse(sn.fits_on_one_line(backed, self.meter))
        self.assertTrue(turned.rotated)
        self.assertFalse(sn.fits_on_one_line(turned, self.meter))

    def test_single_line_cells_names_only_cells_that_fit(self) -> None:
        text = document(html_label("short", "Customer", width=96),
                        html_label("long", "A long label that must wrap across several lines", width=96),
                        native_label("native", "<tspan>x</tspan>"))
        self.assertEqual(sn.single_line_cells(text, self.meter), {"short"})


class NativeCopyTests(unittest.TestCase):
    SOURCE = ('<mxfile><diagram id="d"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>\n'
              '<mxCell id="a" value="One" style="text;html=1;whiteSpace=wrap;align=left;" vertex="1" parent="1"/>\n'
              '<mxCell id="b" value="Two" style="text;html=1;align=left;" vertex="1" parent="1"/>\n'
              '<mxCell id="c" value="Three" style="text;html=1;whiteSpace=wrap;" vertex="1" parent="1"/>\n'
              '<mxCell id="d" value="Four" style="text;whiteSpace=wrap;" vertex="1" parent="1"/>\n'
              '<mxCell id="e" value="" style="text;html=1;whiteSpace=wrap;" vertex="1" parent="1"/>\n'
              '</root></mxGraphModel></diagram></mxfile>')

    def test_only_the_named_html_cells_with_a_label_are_converted(self) -> None:
        converted = sn.native_labels_copy(self.SOURCE, {"a", "b", "d", "e"})
        self.assertIn('style="text;html=1;whiteSpace=wrap;align=left;convertToSvg=1;svgWhiteSpace=wrap;"', converted)
        self.assertIn('style="text;html=1;align=left;convertToSvg=1;"', converted)
        self.assertIn('id="c" value="Three" style="text;html=1;whiteSpace=wrap;"', converted)   # not named
        self.assertIn('id="d" value="Four" style="text;whiteSpace=wrap;"', converted)           # not html=1
        self.assertIn('id="e" value="" style="text;html=1;whiteSpace=wrap;"', converted)        # no label

    def test_nothing_else_changes_and_a_second_pass_changes_nothing(self) -> None:
        once = sn.native_labels_copy(self.SOURCE, {"a"})
        self.assertEqual(once.replace("convertToSvg=1;svgWhiteSpace=wrap;", ""), self.SOURCE)
        self.assertEqual(sn.native_labels_copy(once, {"a"}), once)

    def test_no_cells_leaves_the_text_identical(self) -> None:
        self.assertEqual(sn.native_labels_copy(self.SOURCE, set()), self.SOURCE)


try:
    import numpy as np
except ImportError:  # CI installs no NumPy: the pixel comparison is a local tool
    np = None


@unittest.skipIf(np is None, "NumPy is not installed")
class LabComparisonTests(unittest.TestCase):
    def picture(self, *blobs: tuple[int, int]):
        image = np.full((60, 80), 255, dtype=np.int16)
        for y, x in blobs:
            image[y:y + 8, x:x + 20] = 40
        return image

    def test_a_text_edge_one_pixel_off_is_not_a_difference(self) -> None:
        metrics = svg_lab.pixel_metrics(self.picture((10, 10)), self.picture((11, 10)))
        self.assertEqual(metrics["mismatch_pct"], 0.0)
        self.assertGreater(metrics["raw_diff_pct"], 0.0)

    def test_a_word_that_moved_or_vanished_is_one(self) -> None:
        moved = svg_lab.pixel_metrics(self.picture((10, 10)), self.picture((10, 40)))
        vanished = svg_lab.pixel_metrics(self.picture((10, 10), (30, 10)), self.picture((10, 10)))
        self.assertGreater(moved["mismatch_pct"], 50)
        self.assertGreater(vanished["mismatch_pct"], 30)

    def test_pictures_of_different_sizes_are_reported_not_compared(self) -> None:
        metrics = svg_lab.pixel_metrics(self.picture((10, 10)), self.picture((10, 10))[:50])
        self.assertFalse(metrics["same_size"])


class LabHelperTests(unittest.TestCase):
    def test_the_text_only_copy_hides_shapes_and_keeps_the_label(self) -> None:
        text = svg_lab.text_only(document(StripTests.SHAPE, native_label("c2", "<tspan>x</tspan>")))
        self.assertIn("{display:none}", text)
        self.assertLess(text.index("<style>"), text.index("<rect"))
        self.assertIn("<text", text)

    def test_the_export_rules_name_what_a_figure_must_not_have(self) -> None:
        good = document(native_label("c2", "<tspan>x</tspan>"))
        self.assertEqual(svg_lab.export_rules(good.replace("<svg ", '<svg style="background-color: #FFFFFF; color-scheme: light;" ', 1), good), [])
        problems = svg_lab.export_rules(good.replace("fill=\"#2C3E50\"", "fill=\"light-dark(#000, #fff)\""), good)
        self.assertIn("light-dark() colors", problems)

    def test_a_chapter_is_read_from_a_figure_name(self) -> None:
        self.assertEqual([svg_lab.chapter_of(n) for n in ("fig-03-07-x", "fig-b-02-y", "cover")], ["03", "b", "other"])


if __name__ == "__main__":
    unittest.main()
