"""The EPUB and DOCX checks of scripts/ebook_validate.py, on small files made here (no book build needed)."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from scripts import ebook_validate as ev  # noqa: E402


def png(width: int = 1728, height: int = 787, mode: str = "RGB") -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, (width, height), "white" if mode == "RGB" else 0).save(buffer, "PNG")
    return buffer.getvalue()


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'


def make_epub(path: Path, *, image: str = "png", compress_mimetype: bool = False, mimetype_first: bool = True,
              missing_image: bool = False, bad_anchor: bool = False, text: str = "Body.", orphan: bool = False,
              wrong_type: bool = False, bad_xml: bool = False, spine_missing: bool = False,
              figures: int = 1) -> Path:
    ext = "svg" if image == "svg" else "png"
    media_type = "image/svg+xml" if ext == "svg" else ("image/jpeg" if wrong_type else "image/png")
    imgs = "".join(f'<figure><img src="../media/file{i}.{ext}" alt="Figure {i}"/><figcaption>Cap {i}</figcaption></figure>'
                   for i in range(figures))
    anchor = "nowhere" if bad_anchor else "sec"
    chapter1 = (f'<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml"><body><p>{text}</p>{imgs}'
                f'<p><a href="ch002.xhtml#{anchor}">next</a></p></body></html>')
    if bad_xml:
        chapter1 = chapter1.replace("</body>", "")
    chapter2 = '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml"><body><h2 id="sec">Two</h2></body></html>'
    nav = ('<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">'
           '<body><nav epub:type="toc"><ol><li><a href="text/ch001.xhtml">One</a></li></ol></nav></body></html>')
    items = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
             '<item id="ch1" href="text/ch001.xhtml" media-type="application/xhtml+xml"/>',
             '<item id="ch2" href="text/ch002.xhtml" media-type="application/xhtml+xml"/>',
             '<item id="cover-image" href="media/cover.png" media-type="image/png" properties="cover-image"/>']
    items += [f'<item id="f{i}" href="media/file{i}.{ext}" media-type="{media_type}"/>' for i in range(figures)]
    opf = ('<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="id">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">x</dc:identifier>'
           f'<dc:title>T</dc:title></metadata><manifest>{"".join(items)}</manifest>'
           f'<spine><itemref idref="ch1"/><itemref idref="{"ch9" if spine_missing else "ch2"}"/></spine></package>')
    container = ('<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>'
                 '</rootfiles></container>')
    files = {"META-INF/container.xml": container, "EPUB/content.opf": opf, "EPUB/nav.xhtml": nav,
             "EPUB/text/ch001.xhtml": chapter1, "EPUB/text/ch002.xhtml": chapter2, "EPUB/media/cover.png": png(40, 60)}
    for i in range(figures):
        if not (missing_image and i == 0):
            files[f"EPUB/media/file{i}.{ext}"] = SVG if ext == "svg" else png(200, 100)
    if orphan:
        files["EPUB/media/stray.png"] = png(10, 10)
    with zipfile.ZipFile(path, "w") as archive:
        def put_mimetype() -> None:
            info = zipfile.ZipInfo("mimetype")
            info.compress_type = zipfile.ZIP_DEFLATED if compress_mimetype else zipfile.ZIP_STORED
            archive.writestr(info, "application/epub+zip")
        if mimetype_first:
            put_mimetype()
        for name, data in files.items():
            archive.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        if not mimetype_first:
            put_mimetype()
    return path


def make_docx(path: Path, *, cx: int = 5334000, cy: int = 2429000, image=None, svg: bool = False,
              page: tuple[int, int, int] | None = (12240, 1440, 1440), missing_media: bool = False,
              text: str = "Body.", rid_offset: int = 0, captions: int = 1) -> Path:
    image = image or png(1728, 787)
    rid = f"rId{1 + rid_offset}"
    svg_rid = f"rId{2 + rid_offset}"
    blip = f'<a:blip r:embed="{rid}">' + (
        f'<a:extLst><a:ext uri="{{x}}"><asvg:svgBlip xmlns:asvg="{ev.NS["asvg"]}" r:embed="{svg_rid}"/></a:ext></a:extLst>'
        if svg else "") + "</a:blip>"
    drawing = (f'<w:drawing><wp:inline><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="Picture" descr="A diagram"/>'
               f'<a:graphic><a:graphicData><pic:pic><pic:blipFill>{blip}</pic:blipFill></pic:pic></a:graphicData></a:graphic>'
               f'</wp:inline></w:drawing>')
    caption = "".join(f'<w:p><w:pPr><w:pStyle w:val="ImageCaption"/></w:pPr><w:r><w:t>Figure 1.{i}: Cap</w:t></w:r></w:p>'
                      for i in range(captions))
    sect = (f'<w:sectPr><w:pgSz w:w="{page[0]}" w:h="15840"/><w:pgMar w:left="{page[1]}" w:right="{page[2]}"/></w:sectPr>'
            if page else "<w:sectPr/>")
    ns = " ".join(f'xmlns:{k}="{ev.NS[k]}"' for k in ("w", "wp", "a", "pic", "r"))
    document = (f'<?xml version="1.0"?><w:document {ns}><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p>'
                f'<w:p><w:r>{drawing}</w:r></w:p>{caption}{sect}</w:body></w:document>')
    rels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            'Target="media/image1.png"/>'
            + (f'<Relationship Id="{svg_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
               'Target="media/image1.svg"/>' if svg else "")
            + '<Relationship Id="rId99" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
              'Target="https://example.org/" TargetMode="External"/></Relationships>')
    types = ('<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="png" ContentType="image/png"/><Default Extension="svg" ContentType="image/svg+xml"/>'
             '<Override PartName="/word/document.xml" '
             'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    root_rels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                 'officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", rels)
        archive.writestr("docProps/core.xml", "<cp:coreProperties xmlns:cp='x' xmlns:dcterms='y'><dcterms:modified>1</dcterms:modified></cp:coreProperties>")
        if not missing_media:
            archive.writestr("word/media/image1.png", image)
            if svg:
                archive.writestr("word/media/image1.svg", SVG)
    return path


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="ebook check ")
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)


class EpubTests(TempCase):
    def test_a_well_formed_epub_passes(self) -> None:
        report = ev.validate_epub(make_epub(self.dir / "a.epub", figures=3), expect_figures=3)
        self.assertEqual(report.errors, [])
        self.assertEqual((report.info["figure_images"], report.info["png_files"], report.info["svg_files"]), (3, 4, 0))
        self.assertEqual(report.info["image_modes"], {"RGB": 3})

    def test_mimetype_must_be_first_and_stored(self) -> None:
        self.assertTrue(any("compressed" in e for e in
                            ev.validate_epub(make_epub(self.dir / "a.epub", compress_mimetype=True)).errors))
        self.assertTrue(any("first ZIP entry" in e for e in
                            ev.validate_epub(make_epub(self.dir / "b.epub", mimetype_first=False)).errors))

    def test_svg_diagrams_are_an_error_unless_allowed(self) -> None:
        path = make_epub(self.dir / "a.epub", image="svg", figures=2)
        errors = ev.validate_epub(path).errors
        self.assertTrue(any("SVG diagram" in e for e in errors))
        self.assertTrue(any("manifest still lists the SVG" in e for e in errors))
        self.assertEqual(ev.validate_epub(path, allow_svg=True).errors, [])

    def test_a_missing_image_is_found(self) -> None:
        errors = ev.validate_epub(make_epub(self.dir / "a.epub", missing_image=True, figures=2)).errors
        self.assertTrue(any("not in the archive" in e for e in errors))
        self.assertTrue(any("do not resolve" in e for e in errors))

    def test_a_dead_internal_link_is_found(self) -> None:
        errors = ev.validate_epub(make_epub(self.dir / "a.epub", bad_anchor=True)).errors
        self.assertTrue(any("internal link" in e for e in errors))

    def test_a_wrong_media_type_the_spine_and_broken_xml_are_found(self) -> None:
        self.assertTrue(any("declared as" in e for e in
                            ev.validate_epub(make_epub(self.dir / "a.epub", wrong_type=True)).errors))
        self.assertTrue(any("spine refers" in e for e in
                            ev.validate_epub(make_epub(self.dir / "b.epub", spine_missing=True)).errors))
        self.assertTrue(any("not well-formed" in e for e in
                            ev.validate_epub(make_epub(self.dir / "c.epub", bad_xml=True)).errors))

    def test_orphans_warn_and_the_figure_count_is_checked(self) -> None:
        report = ev.validate_epub(make_epub(self.dir / "a.epub", orphan=True), expect_figures=2)
        self.assertTrue(any("not in the manifest" in w for w in report.warnings))
        self.assertTrue(any("2 expected" in e for e in report.errors))

    def test_a_file_that_is_not_a_zip_is_an_error(self) -> None:
        path = self.dir / "bad.epub"
        path.write_bytes(b"not a zip")
        self.assertTrue(any("not a readable ZIP" in e for e in ev.validate_epub(path).errors))

    def test_comparison_ignores_only_the_diagram_files(self) -> None:
        old = make_epub(self.dir / "old.epub", image="svg", figures=2)
        new = make_epub(self.dir / "new.epub", image="png", figures=2)
        self.assertEqual(ev.compare_epub(old, new).errors, [])
        changed = make_epub(self.dir / "changed.epub", image="png", figures=2, text="Different body.")
        errors = ev.compare_epub(old, changed).errors
        self.assertTrue(any("differ from the earlier EPUB" in e for e in errors), errors)

    def test_epubcheck_is_reported_as_not_run_when_missing(self) -> None:
        report = ev.validate_epub(make_epub(self.dir / "a.epub"))
        from unittest.mock import patch
        with patch("shutil.which", return_value=None), patch.dict("os.environ", {}, clear=True):
            ev.run_epubcheck(self.dir / "a.epub", report)
        self.assertIn("not run", report.info["epubcheck"])


class DocxTests(TempCase):
    def test_a_well_formed_docx_passes(self) -> None:
        report = ev.validate_docx(make_docx(self.dir / "a.docx"), expect_figures=1)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.info["pictures"], 1)
        self.assertAlmostEqual(report.info["min_ppi"], 1728 / (5334000 / 914400), places=0)
        self.assertEqual(report.info["captions"], 1)

    def test_a_stretched_picture_is_found(self) -> None:
        errors = ev.validate_docx(make_docx(self.dir / "a.docx", cy=3000000)).errors
        self.assertTrue(any("stretched" in e for e in errors))

    def test_a_picture_wider_than_the_text_column_is_found(self) -> None:
        errors = ev.validate_docx(make_docx(self.dir / "a.docx", cx=6400000, cy=2915000)).errors
        self.assertTrue(any("wider than the text column" in e for e in errors))

    def test_the_page_setup_decides_the_column(self) -> None:
        narrow = make_docx(self.dir / "a.docx", page=(12240, 2880, 2880))
        self.assertTrue(any("wider than the text column" in e for e in ev.validate_docx(narrow).errors))

    def test_svg_pictures_are_an_error_unless_allowed(self) -> None:
        path = make_docx(self.dir / "a.docx", svg=True)
        errors = ev.validate_docx(path).errors
        self.assertTrue(any("svgBlip" in e for e in errors))
        self.assertTrue(any("still contains the SVG" in e for e in errors))
        self.assertEqual(ev.validate_docx(path, allow_svg=True).errors, [])

    def test_a_missing_media_part_is_found(self) -> None:
        errors = ev.validate_docx(make_docx(self.dir / "a.docx", missing_media=True)).errors
        self.assertTrue(any("not in the archive" in e for e in errors))
        self.assertTrue(any("do not resolve" in e for e in errors))

    def test_a_low_resolution_warns(self) -> None:
        report = ev.validate_docx(make_docx(self.dir / "a.docx", image=png(800, 364), cy=2429000))
        self.assertTrue(any("print below" in w for w in report.warnings))

    def test_a_palette_png_is_read(self) -> None:
        buffer = io.BytesIO()
        Image.new("P", (1728, 787), 0).save(buffer, "PNG")
        report = ev.validate_docx(make_docx(self.dir / "a.docx", image=buffer.getvalue()))
        self.assertEqual(report.info["image_modes"], {"P": 1})

    def test_a_damaged_image_is_found(self) -> None:
        errors = ev.validate_docx(make_docx(self.dir / "a.docx", image=b"junk")).errors
        self.assertTrue(any("not a readable image" in e for e in errors))

    def test_the_figure_count_is_checked(self) -> None:
        self.assertTrue(any("165 expected" in e for e in
                            ev.validate_docx(make_docx(self.dir / "a.docx"), expect_figures=165).errors))

    def test_comparison_ignores_picture_parts_and_relationship_numbers(self) -> None:
        old = make_docx(self.dir / "old.docx", svg=True)
        new = make_docx(self.dir / "new.docx", rid_offset=3)
        self.assertEqual(ev.compare_docx(old, new).errors, [])

    def test_comparison_finds_changed_text_and_resized_pictures(self) -> None:
        old = make_docx(self.dir / "old.docx")
        self.assertTrue(any("beyond the pictures" in e for e in
                            ev.compare_docx(old, make_docx(self.dir / "t.docx", text="Other.")).errors))
        errors = ev.compare_docx(old, make_docx(self.dir / "s.docx", cx=5000000, cy=2277000)).errors
        self.assertTrue(any("changed size" in e for e in errors))


class CommandLineTests(TempCase):
    def test_exit_status_follows_the_checks(self) -> None:
        good = make_epub(self.dir / "good.epub")
        bad = make_epub(self.dir / "bad.epub", image="svg")
        self.assertEqual(ev.main(["--epub", str(good)]), 0)
        self.assertEqual(ev.main(["--epub", str(bad)]), 1)
        report = self.dir / "report.json"
        ev.main(["--epub", str(good), "--docx", str(make_docx(self.dir / "g.docx")), "--report", str(report)])
        import json
        self.assertEqual([r["kind"] for r in json.loads(report.read_text(encoding="utf-8"))], ["epub", "docx"])


if __name__ == "__main__":
    unittest.main()
