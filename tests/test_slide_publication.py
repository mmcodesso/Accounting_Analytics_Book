"""Packaging and disclosure regressions, runnable with stdlib unittest."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.slides.export_public import DEFAULT_BUILD_FILES, export_public
from scripts.slides.verify import (audit_text, safe_path, sha256, source_sha256, verify_local_links,
                                  verify_outputs, verify_pptx, verify_sources)


SLIDE = """---
title: Teaching pilot
---

## Evidence

Interpret the result before recommending a solution.

::: {.notes}
Purpose: explain evidence. Narration: compare the two periods. Pause: what changed?
:::
"""


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def fixture(root: Path, *, status: str = "approved") -> dict:
    write(root, "slides/chapter-01/index.qmd", SLIDE)
    book = write(root, "chapters/01/chapter.qmd", "# Book\n\nPublic chapter.\n<!-- Instructor answer: private computation. -->\n")
    write(root, "slides/_quarto.yml", json.dumps({"project": {"type": "default", "render": ["chapter-01/index.qmd"]}}))
    write(root, "slides/theme/tokens.yml", json.dumps({"colors": {"blue": "#123456"}}))
    for rel in DEFAULT_BUILD_FILES:
        write(root, rel, "# public build input\n")
    manifest = {
        "version": 1, "book_url": "https://example.org/book", "chapters": [{
            "id": "chapter-01", "number": 1, "source": "chapter-01/index.qmd", "status": status,
            "book_sources": ["chapters/01/chapter.qmd"],
            "reviewed_source_hashes": {"chapters/01/chapter.qmd": source_sha256(book)},
        }], "public_assets": [], "public_fragments": [],
    }
    write(root, "slides/manifest.yml", json.dumps(manifest))
    return manifest


def make_pptx(path: Path, *, notes: str = "Public narration explains the evidence and invites a pause.",
              table: bool = True, media: bool = True, broken: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    opening = ('<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
               'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">')
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", opening + "<a:t>Editable title</a:t>" +
                         ("<a:tbl><a:tr><a:tc><a:t>42.26%</a:t></a:tc></a:tr></a:tbl>" if table else "") + "</p:sld>")
        archive.writestr("ppt/notesSlides/notesSlide1.xml", opening + f"<a:t>{notes}</a:t></p:sld>")
        target = "missing.png" if broken else "figure.png"
        if media:
            archive.writestr("ppt/media/figure.png", b"png fixture")
            archive.writestr("ppt/slides/_rels/slide1.xml.rels",
                             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                             f'<Relationship Target="../media/{target}" Id="rId1" Type="image"/></Relationships>')


class SlideSourceTests(unittest.TestCase):
    def test_specific_disclosure_markers_do_not_reject_pedagogic_solution(self) -> None:
        self.assertEqual([], audit_text("Compare alternative solutions to the business question.", "slide"))
        self.assertTrue(audit_text("Instructor answer: revenue is 400.", "slide"))
        self.assertTrue(audit_text("<!-- ordinary author-only comment -->", "slide"))
        self.assertEqual([], audit_text("<!-- generated: public figure -->", "slide"))
        self.assertTrue(audit_text("<!-- generated: instructor answer -->", "slide"))

    def test_cross_platform_traversal_and_private_inputs_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in ("../secret", "C:\\Users\\name\\secret", "/private", "slides/../../private", "slides\\..\\private"):
                with self.subTest(rel=rel), self.assertRaises(ValueError):
                    safe_path(root, rel, public=True)
            for rel in ("datasets/book.sqlite", "scripts/companion/build.py", "facts/answers.json"):
                with self.subTest(rel=rel), self.assertRaises(ValueError):
                    safe_path(root, rel, public=True)

    def test_source_review_hash_and_notes_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root)
            self.assertEqual([], verify_sources(root, manifest))
            write(root, "chapters/01/chapter.qmd", "changed meaning")
            self.assertTrue(any("editorial review" in error for error in verify_sources(root, manifest)))
            write(root, "slides/chapter-01/index.qmd", "## Evidence\nNo notes\n")
            self.assertTrue(any("no public notes" in error for error in verify_sources(root, manifest)))

    def test_review_hash_survives_git_newline_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root)
            book = root / "chapters/01/chapter.qmd"
            text = book.read_text(encoding="utf-8")
            book.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual([], verify_sources(root, manifest))
            book.write_bytes(text.encode("utf-8"))
            self.assertEqual([], verify_sources(root, manifest))


class ArtifactTests(unittest.TestCase):
    def test_packaged_html_css_links_and_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, "slides/chapter-01/index.html", '<link href="../../site_libs/theme.css"><img src="/book/figure.svg"><a href="https://example.org">Book</a>')
            write(root, "site_libs/theme.css", 'body { background: url("../figure.svg"); }')
            write(root, "figure.svg", "<svg/>")
            self.assertEqual([], verify_local_links(root, book_url="https://example.org/book"))
            (root / "figure.svg").unlink()
            self.assertEqual(2, len(verify_local_links(root, book_url="https://example.org/book")))
            write(root, "escape.html", '<img src="../secret.png">')
            self.assertTrue(any("escapes" in error for error in verify_local_links(root)))

    def test_pptx_checks_real_zip_text_tables_notes_and_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pptx = Path(temp) / "pilot.pptx"
            make_pptx(pptx)
            self.assertEqual([], verify_pptx(pptx, require_table=True, require_media=True))
            self.assertTrue(any('unintended slides' in error for error in
                                verify_pptx(pptx, expected_slides=2)))
            make_pptx(pptx, table=False, notes="1", broken=True)
            errors = verify_pptx(pptx, require_table=True)
            self.assertTrue(any("native editable table" in error for error in errors))
            self.assertTrue(any("populated notes" in error for error in errors))
            self.assertTrue(any("broken package relationship" in error for error in errors))
            make_pptx(pptx, notes="Instructor answer: protected exercise calculation")
            self.assertTrue(any("private-material marker" in error for error in verify_pptx(pptx)))

    def test_site_rejects_pilot_or_removed_deck(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root, status="pilot")
            write(root, "_book/slides/chapter-01/index.html", "<html></html>")
            self.assertTrue(any("Unapproved or removed" in error for error in verify_outputs(root, manifest, root / "_book")))


class ExportTests(unittest.TestCase):
    def test_export_sanitizes_book_sources_and_follows_includes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root)
            book = write(root, "chapters/01/chapter.qmd", "# Book\n{{< include _exercise.qmd >}}\n<!-- Instructor answer: 42 -->")
            write(root, "chapters/01/_exercise.qmd", "Public question.\n<!-- Answer key: secret -->")
            manifest["chapters"][0]["reviewed_source_hashes"]["chapters/01/chapter.qmd"] = source_sha256(book)
            destination = export_public(root, manifest)
            self.assertNotIn("secret", (destination / "chapters/01/_exercise.qmd").read_text())
            self.assertNotIn("Instructor", (destination / "chapters/01/chapter.qmd").read_text())
            exported = json.loads((destination / "slides/manifest.yml").read_text())
            self.assertEqual([], verify_sources(destination, exported))
            report = json.loads((destination / "export-manifest.json").read_text())
            self.assertFalse(report["review_only"])
            self.assertEqual("not run", report["validation"]["clean_public_checkout"])
            self.assertFalse((destination / "datasets").exists())

    def test_public_export_excludes_pilot_and_review_export_labels_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root, status="pilot")
            public = export_public(root, manifest)
            self.assertFalse((public / "slides/chapter-01/index.qmd").exists())
            self.assertEqual([], json.loads((public / "slides/_quarto.yml").read_text())["project"]["render"])
            review = export_public(root, manifest, root / "outputs/pilot-review", include_pilot=True)
            self.assertTrue((review / "slides/chapter-01/index.qmd").is_file())
            self.assertIn("REVIEW ONLY", (review / "TRANSFER.md").read_text())

    def test_root_relative_book_image_includes_editable_and_print_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root)
            book = write(root, "chapters/01/chapter.qmd", "# Book\n![Figure](/visuals/svg/example.svg)\n"
                         "[Generated download](/downloads/book-latest.pdf)\n")
            manifest["chapters"][0]["reviewed_source_hashes"]["chapters/01/chapter.qmd"] = source_sha256(book)
            write(root, "visuals/svg/example.svg", "<svg/>")
            write(root, "visuals/src/example.drawio", "<mxfile/>")
            write(root, "visuals/pdf/example.pdf", "pdf fixture")
            destination = export_public(root, manifest)
            for rel in ("visuals/svg/example.svg", "visuals/src/example.drawio", "visuals/pdf/example.pdf"):
                self.assertTrue((destination / rel).is_file(), rel)
            self.assertFalse((destination / "downloads").exists())

    def test_removed_deck_inventory_and_owned_export_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root)
            destination = export_public(root, manifest)
            previous = write(root, "previous.json", (destination / "export-manifest.json").read_text())
            manifest["chapters"][0]["status"] = "deferred"
            destination = export_public(root, manifest, previous_manifest=previous)
            report = json.loads((destination / "export-manifest.json").read_text())
            self.assertIn("slides/chapter-01/index.qmd", report["remove_files"])
            self.assertFalse((destination / "slides/chapter-01/index.qmd").exists())
            write(destination, "user-file.txt", "preserve")
            with self.assertRaisesRegex(ValueError, "Untracked"):
                export_public(root, manifest)
            self.assertTrue((destination / "user-file.txt").exists())

    def test_private_include_and_destination_outside_outputs_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = fixture(root)
            manifest["public_book_files"] = ["book-extra.qmd"]
            write(root, "book-extra.qmd", "{{< include facts/answers.qmd >}}")
            write(root, "facts/answers.qmd", "private")
            with self.assertRaisesRegex(ValueError, "Private path"):
                export_public(root, manifest)
            with self.assertRaisesRegex(ValueError, "inside this repository"):
                export_public(root, manifest, root / "some-source-folder")

    def test_public_checkout_check_uses_disposable_dataset_free_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "authoring"
            manifest = fixture(root)
            write(root, "scripts/build_all.py", "from pathlib import Path\n"
                  "assert not Path('datasets').exists()\n"
                  "assert not Path('facts').exists()\n"
                  "assert not Path('slides/obsolete.qmd').exists()\n"
                  "assert Path('slides/chapter-01/index.qmd').is_file()\n")
            checkout = Path(temp) / "public"
            write(checkout, "_quarto.yml", "{}")
            write(checkout, "datasets/secret.sqlite", "do not access")
            write(checkout, "slides/obsolete.qmd", "old deck")
            destination = export_public(root, manifest, public_checkout=checkout)
            report = json.loads((destination / "export-manifest.json").read_text())
            self.assertTrue(report["validation"]["clean_public_checkout"].startswith("passed"))
            self.assertEqual("do not access", (checkout / "datasets/secret.sqlite").read_text())
            self.assertTrue((checkout / "slides/obsolete.qmd").is_file())


if __name__ == "__main__":
    unittest.main()
