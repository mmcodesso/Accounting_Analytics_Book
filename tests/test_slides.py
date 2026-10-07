"""The slide decks: the book index, the source checks, the build and assembly, and the PowerPoint
finishing. Fake renderers stand in for Quarto, so no Quarto, Draw.io or dataset is needed (the
template test runs only where Quarto is installed)."""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_all
from scripts.slides import book_index, pptx_finish
from scripts.slides import prepare as prep
from scripts.slides.pptx_theme import NS, q
from scripts.slides.verify import (audit_text, crop_key, load_manifest, parse_crop, safe_path, verify_local_links,
                                   verify_outputs, verify_pptx, verify_sources)


def write(root: Path, rel: str, text: str = "fixture") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


BOOK = """book:
  title: "A Test Book"
  chapters:
    - index.qmd
    - part: "Foundations"
      chapters:
        - chapters/01-first/chapter.qmd
        - chapters/02-second/chapter.qmd
"""

CHAPTER = """---
title: "The First Chapter"
---

::: {.learning-objectives}
## Learning Objectives {.unnumbered}

After completing this chapter, you will be able to:

1. Name the parts.
2. Explain the whole.
:::

## Opening Scenario {.unnumbered}

A scenario.

## The Parts

![The Parts Diagram.](/visuals/svg/fig-01-01-parts.svg){#fig-01-01 fig-alt="Three boxes in a row."}

::: {.callout-tip .in-practice icon=false}
## In Practice
Not a section.
:::

| Part | Code |
|------|------|
| One | `a|b` |
| Two \\| more | b |

: The Parts Table {#tbl-01-01}

### A Detail

{{< include _tutorial-01.qmd >}}

## Looking Ahead

{{< include _key-terms.qmd >}}
"""

TUTORIAL = """## Guided Tutorial 1.1: Trying It

**Context and objective.** Try the parts.

**Prerequisites.** A computer.

**Step 1. Open the file.** Open it.

**Step 2. Look around.**

**Checkpoint.** You should be able to answer:

- What is part one? (One.)
- Where is part two?

If you can, go on.
"""

KEY_TERMS = """{{< pagebreak >}}

## Key Terms

{{< include /shared/fragments/_term.qmd >}}

**Part.** A piece of the whole.
"""

DECK = """## In this chapter

::: {.roadmap}
:::

::: {.notes}
The chapter has two modules; this slide lists them.
:::

# The Parts

## The parts fit together

{{< book-figure fig-01-01 >}}

::: {.notes}
Walk through the three boxes from left to right.
:::

## Two parts at a glance

{{< book-table tbl-01-01 >}}

::: {.notes}
Each row of the table names one part and its code.
:::
"""


def book_fixture(root: Path) -> None:
    write(root, "_quarto.yml", BOOK)
    write(root, "index.qmd", "# Home\n")
    write(root, "chapters/01-first/chapter.qmd", CHAPTER)
    write(root, "chapters/01-first/_tutorial-01.qmd", TUTORIAL)
    write(root, "chapters/01-first/_key-terms.qmd", KEY_TERMS)
    write(root, "shared/fragments/_term.qmd", "**Analytics.** The use of data.\n")
    write(root, "chapters/02-second/chapter.qmd", '---\ntitle: "The Second Chapter"\n---\n\n## Basics\n')
    write(root, "slides/chapter-01/index.qmd", DECK)


class BookIndexTests(unittest.TestCase):
    def test_chapter_one_comes_straight_from_the_book(self) -> None:
        index = book_index.build(ROOT)
        chapter = index["chapters"]["chapter-01"]
        self.assertEqual("The Role of Analytics in Accounting", chapter["title"])
        self.assertEqual("Part I: Foundations of Accounting Analytics", chapter["part"])
        self.assertEqual(5, len(chapter["objectives"]))
        numbered = [s["number"] for s in chapter["sections"] if s["level"] == 2][:9]
        self.assertEqual([f"1.{n}" for n in range(1, 10)], numbered)
        self.assertEqual([f"1.{n}" for n in range(1, 9)], [f["number"] for f in chapter["figures"]])
        self.assertEqual("1.2", index["tables"]["tbl-01-02"]["number"])
        self.assertEqual(7, len(chapter["tutorials"][0]["steps"]))
        self.assertEqual(6, len(chapter["exercises"]))
        self.assertEqual("Chapter 2: Understanding Data in Accounting", chapter["next"])

    def test_includes_sections_figures_tables_and_tutorials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            index = book_index.build(root)
            chapter = index["chapters"]["chapter-01"]
            self.assertEqual("Part I: Foundations", chapter["part"])
            self.assertEqual(["Name the parts.", "Explain the whole."], chapter["objectives"])
            self.assertEqual([("1.1", "The Parts"), ("1.1.1", "A Detail"),
                              ("1.2", "Guided Tutorial 1.1: Trying It"), ("1.3", "Looking Ahead"),
                              ("1.4", "Key Terms")],
                             [(s["number"], s["title"]) for s in chapter["sections"]])
            figure = index["figures"]["fig-01-01"]
            self.assertEqual(("1.1", "The Parts Diagram", "Three boxes in a row."),
                             (figure["number"], figure["caption"], figure["alt"]))
            table = index["tables"]["tbl-01-01"]
            self.assertEqual(["Part", "Code"], table["header"])
            self.assertEqual([["One", "`a|b`"], ["Two \\| more", "b"]], table["rows"])
            tutorial = chapter["tutorials"][0]
            self.assertEqual(["Open the file", "Look around"], [s["title"] for s in tutorial["steps"]])
            self.assertEqual(2, len(tutorial["checkpoint"]["items"]))
            self.assertEqual("If you can, go on.", tutorial["checkpoint"]["close"])
            self.assertEqual(["Analytics", "Part"], chapter["key_terms"])
            self.assertEqual("Chapter 2: The Second Chapter", chapter["next"])
            self.assertEqual([1, 2], chapter["part_chapters"])


class SourceCheckTests(unittest.TestCase):
    def check(self, root: Path) -> tuple[list[str], list[str]]:
        return verify_sources(root, prep.deck_ids(root), book_index.build(root))

    def test_a_clean_deck_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            self.assertEqual(([], []), self.check(root))

    def test_editing_the_chapter_never_blocks_the_deck(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            chapter = root / "chapters/01-first/chapter.qmd"
            chapter.write_text(chapter.read_text(encoding="utf-8").replace("A scenario.", "A new scenario."),
                               encoding="utf-8")
            self.assertEqual([], self.check(root)[0])

    def test_every_slide_needs_useful_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            write(root, "slides/chapter-01/index.qmd", "## No notes\n\nText.\n\n## Short\n\n::: {.notes}\nHi.\n:::\n")
            errors = self.check(root)[0]
            self.assertTrue(any("'No notes' has no notes" in error for error in errors))
            self.assertTrue(any("'Short' has notes too short" in error for error in errors))

    def test_decks_carry_no_yaml_and_no_author_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            write(root, "slides/chapter-01/index.qmd", "---\nauthor: Mauricio Codesso\n---\n\n" + DECK)
            errors = self.check(root)[0]
            self.assertTrue(any("carry no YAML" in error for error in errors))
            self.assertTrue(any("names the author" in error for error in errors))
            # The dataset's GitHub address is not the author's name.
            write(root, "slides/chapter-01/index.qmd",
                  DECK + "\n## Data\n\n<https://github.com/mmcodesso/CharlesRiver_Database>\n\n"
                  "::: {.notes}\nThe dataset has its own repository and documentation.\n:::\n")
            self.assertEqual([], self.check(root)[0])

    def test_citations_must_exist_in_the_book(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            write(root, "slides/chapter-01/index.qmd", DECK.replace("fig-01-01", "fig-01-09")
                  .replace("tbl-01-01", "tbl-09-01") + "\n## Steps\n\n{{< book-steps 1.4 >}}\n\n"
                  "::: {.notes}\nThe steps of a tutorial that does not exist.\n:::\n")
            errors = self.check(root)[0]
            for missing in ("no figure fig-01-09", "no table tbl-09-01", "no Guided Tutorial 1.4"):
                self.assertTrue(any(missing in error for error in errors), missing)

    def test_a_step_range_must_lie_inside_its_tutorial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            slide = "\n## Steps\n\n{{{{< book-steps 1.1 {} >}}}}\n\n::: {{.notes}}\nThe tutorial's steps, in part.\n:::\n"
            write(root, "slides/chapter-01/index.qmd", DECK + slide.format("2-2"))
            self.assertEqual([], self.check(root)[0])
            write(root, "slides/chapter-01/index.qmd", DECK + slide.format("2-5"))
            self.assertTrue(any("has no steps 2-5" in error for error in self.check(root)[0]))

    def test_a_table_row_range_must_lie_inside_its_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            slide = "\n## Rows\n\n{{{{< book-table tbl-01-01 {} >}}}}\n\n::: {{.notes}}\nPart of the table, by position.\n:::\n"
            write(root, "slides/chapter-01/index.qmd", DECK + slide.format("1-2"))
            self.assertEqual([], self.check(root)[0])
            write(root, "slides/chapter-01/index.qmd", DECK + slide.format("2-3"))
            self.assertTrue(any("tbl-01-01 has no rows 2-3" in error for error in self.check(root)[0]))

    def test_a_divider_that_names_no_section_is_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            write(root, "slides/chapter-01/index.qmd", DECK.replace("# The Parts", "# Something Else"))
            errors, warnings = self.check(root)
            self.assertEqual([], errors)
            self.assertTrue(any("'Something Else'" in warning for warning in warnings))

    def test_a_crop_must_lie_inside_its_figure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            write(root, "slides/chapter-01/index.qmd", DECK.replace(
                "{{< book-figure fig-01-01 >}}", '{{< book-figure fig-01-01 crop="0.5,0,0.6,1" >}}'))
            self.assertTrue(any("must lie inside the figure" in error for error in self.check(root)[0]))

    def test_private_markers_and_paths(self) -> None:
        self.assertEqual([], audit_text("Compare alternative solutions to the business question.", "slide"))
        self.assertTrue(audit_text("Instructor answer: revenue is 400.", "slide"))
        self.assertTrue(audit_text("<!-- ordinary author-only comment -->", "slide"))
        self.assertEqual([], audit_text("<!-- generated: public figure -->", "slide"))
        with tempfile.TemporaryDirectory() as temp:
            for rel in ("../secret", "C:\\Users\\name\\secret", "/private", "slides/../../private",
                        "datasets/book.sqlite", "drafts/notes.md"):
                with self.subTest(rel=rel), self.assertRaises(ValueError):
                    safe_path(Path(temp), rel, public=True)


class PrepareTests(unittest.TestCase):
    def test_the_title_slide_names_the_book_and_the_chapter_and_no_author(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            metadata = prep.deck_metadata(book_index.build(root), "chapter-01")
            self.assertEqual("Chapter 1: The First Chapter", metadata["title"])
            self.assertEqual("A Test Book", metadata["subtitle"])
            self.assertNotIn("author", metadata)
            self.assertEqual("chapter-01.pptx", metadata["format"]["pptx"]["output-file"])
            self.assertEqual("Chapter 1 · The First Chapter", metadata["format"]["revealjs"]["footer"])

    def test_metadata_follows_the_decks_that_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            stale = write(root, "slides/chapter-02/_metadata.yml", "{}")
            index = book_index.build(root)
            prep.write_metadata(root, index, prep.deck_ids(root))
            self.assertFalse(stale.exists())
            written = (root / "slides/chapter-01/_metadata.yml").read_text(encoding="utf-8")
            self.assertEqual("chapter-01", load_manifest(root / "slides/chapter-01/_metadata.yml")["book-chapter"])
            self.assertIn("Generated", written.splitlines()[0])
            self.assertEqual([("fig-01-01", None)], prep.cited_figures(root, ["chapter-01"]))

    def test_crops_are_parsed_named_and_cited_once(self) -> None:
        self.assertEqual((0, 0.25, 1, 0.5), parse_crop("0, 0.25, 1, 0.5"))
        self.assertEqual("0-0p25-1-0p5", crop_key((0, 0.25, 1, 0.5)))
        for bad in ("0,0,1", "0,0,0,1", "a,b,c,d", "0.6,0,0.5,1"):
            with self.subTest(crop=bad), self.assertRaises(ValueError):
                parse_crop(bad)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book_fixture(root)
            deck = DECK + '\n## Detail\n\n{{< book-figure fig-01-01 crop="0,0,0.5,1" >}}\n\n' \
                          '::: {.notes}\nThe left half of the figure, enlarged.\n:::\n'
            write(root, "slides/chapter-01/index.qmd", deck + deck[deck.index("## Detail"):])
            self.assertEqual([("fig-01-01", None), ("fig-01-01", (0, 0, 0.5, 1))],
                             prep.cited_figures(root, ["chapter-01"]))

    def test_an_svg_crop_narrows_the_view_box(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = write(Path(temp), "figure.svg", '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" '
                           'width="800px" height="600px" viewBox="-0.5 -0.5 800 600"><rect width="10"/>'
                           '<foreignObject width="100%" height="100%"><div/></foreignObject></svg>')
            target = Path(temp) / "crop.svg"
            prep.crop_svg(source, target, (0.25, 0.5, 0.5, 0.5))
            root = ET.fromstring(target.read_text(encoding="utf-8"))
            self.assertEqual("199.5 299.5 400 300", root.get("viewBox"))
            self.assertEqual(("400px", "300px"), (root.get("width"), root.get("height")))
            self.assertEqual("10", root[0].get("width"))
            # A label box keeps the whole figure's size, so labels low in the figure are still drawn.
            self.assertEqual(("800", "600"), (root[1].get("width"), root[1].get("height")))

    def test_background_images_are_valid_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bg.png"
            prep.solid_png(path, 40, 10, "FFFFFF", "1A5276", 4)
            data = path.read_bytes()
            self.assertEqual((40, 10), struct.unpack(">II", data[16:24]))
            idat = data.index(b"IDAT")
            length = struct.unpack(">I", data[idat - 4:idat])[0]
            rows = zlib.decompress(data[idat + 4:idat + 4 + length])
            self.assertEqual(10 * (1 + 40 * 3), len(rows))
            self.assertEqual(bytes.fromhex("1A5276"), rows[1:4])
            self.assertEqual(bytes.fromhex("FFFFFF"), rows[-3:])


class PowerPointTests(unittest.TestCase):
    TOKENS = {"colors": {"blue": "1A5276", "tint": "EAF2F8", "paper": "FFFFFF", "ink": "2C3E50",
                         "rule": "D5D8DC"}}

    def test_tables_get_the_book_look_and_stay_native(self) -> None:
        cell = '<a:tc><a:txBody><a:bodyPr/><a:p><a:r><a:rPr/><a:t>{}</a:t></a:r></a:p></a:txBody><a:tcPr/></a:tc>'
        xml = (f'<a:tbl xmlns:a="{NS["a"]}"><a:tblPr firstRow="1"><a:tableStyleId>{{X}}</a:tableStyleId></a:tblPr>'
               + ''.join(f'<a:tr>{cell.format(text)}</a:tr>' for text in ('Head', 'One', 'Two')) + '</a:tbl>')
        table = ET.fromstring(xml)
        pptx_finish.format_table(table, self.TOKENS["colors"])
        self.assertIsNone(table.find('a:tblPr/a:tableStyleId', NS))
        fills = [row.find('a:tc/a:tcPr/a:solidFill/a:srgbClr', NS).get('val') for row in table.findall('a:tr', NS)]
        self.assertEqual(["1A5276", "EAF2F8", "FFFFFF"], fills)
        header_run = table.find('a:tr/a:tc//a:rPr', NS)
        self.assertEqual("1", header_run.get("b"))
        self.assertEqual("FFFFFF", header_run.find('a:solidFill/a:srgbClr', NS).get('val'))

    def test_a_long_caption_takes_its_room_from_the_picture(self) -> None:
        def slide(caption: str) -> ET.Element:
            return ET.fromstring(
                f'<p:sld xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}"><p:cSld><p:spTree>'
                '<p:pic><p:spPr><a:xfrm><a:off x="3000000" y="1400000"/><a:ext cx="5000000" cy="4000000"/></a:xfrm>'
                '</p:spPr></p:pic><p:sp><p:nvSpPr><p:cNvPr id="1" name="TextBox 3"/><p:cNvSpPr txBox="1"/></p:nvSpPr>'
                '<p:spPr><a:xfrm><a:off x="546100" y="5400000"/><a:ext cx="11087100" cy="508000"/></a:xfrm></p:spPr>'
                f'<p:txBody><a:p><a:r><a:rPr/><a:t>{caption}</a:t></a:r></a:p></p:txBody></p:sp>'
                '</p:spTree></p:cSld></p:sld>')
        tokens = {"colors": {"gray": "5D6D7E"}, "sizes": {"evidence": 20}}
        short, long = slide("Figure 3.7 · A caption that fits"), slide("Figure 3.9 · " + "A long caption " * 8)
        for xml in (short, long):
            pptx_finish.format_captions(xml, tokens)
        self.assertEqual("4000000", short.find('.//p:pic//a:ext', NS).get("cy"))
        picture, box = long.find('.//p:pic//a:xfrm', NS), long.find('.//p:sp//a:xfrm', NS)
        extra = 20 * 1.2 * 12700
        self.assertEqual(str(round(4000000 - extra)), picture.find('a:ext', NS).get("cy"))
        self.assertEqual(str(round(5400000 - extra)), box.find('a:off', NS).get("y"))
        center = 2 * int(picture.find('a:off', NS).get("x")) + int(picture.find('a:ext', NS).get("cx"))
        self.assertAlmostEqual(2 * 3000000 + 5000000, center, delta=1)
        self.assertEqual("2000", long.find('.//a:rPr', NS).get("sz"))

    def test_list_numbers_take_the_body_font_and_room_for_two_digits(self) -> None:
        def slide(start: int, first_run: str) -> ET.Element:
            item = ('<a:p><a:pPr marL="342900" indent="-342900"><a:buAutoNum type="arabicPeriod"'
                    f' startAt="{start}"/></a:pPr>{first_run}</a:p>')
            return ET.fromstring(f'<p:sld xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}"><p:cSld><p:spTree><p:sp>'
                                 f'<p:txBody>{item * 3}</p:txBody></p:sp></p:spTree></p:cSld></p:sld>')
        tokens = {"font": "Arial", "code_font": "Consolas", "sizes": {"body": 24}}
        code = '<a:r><a:rPr><a:latin typeface="Consolas"/></a:rPr><a:t>A2</a:t></a:r>'
        text = '<a:r><a:rPr/><a:t>Step</a:t></a:r>'
        plain, coded, long = slide(1, text), slide(1, code), slide(9, text)
        for xml in (plain, coded, long):
            pptx_finish.format_lists(xml, tokens)
        first = plain.find('.//a:pPr', NS)
        self.assertEqual("Arial", first.find('a:buFont', NS).get("typeface"))
        self.assertEqual(["buFont", "buAutoNum"], [child.tag.split("}")[1] for child in first])
        self.assertEqual("342900", first.get("marL"))   # one Arial digit fits the indent Pandoc gives
        self.assertLess(342900, int(coded.find('.//a:pPr', NS).get("marL")))   # a code-font number is wider
        self.assertLess(342900, int(long.find('.//a:pPr', NS).get("marL")))    # and so are 10 and 11

    @unittest.skipUnless(shutil.which("quarto"), "needs Quarto for Pandoc's default template")
    def test_the_template_carries_footer_backgrounds_and_no_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = prep.pandoc_reference(shutil.which("quarto"), Path(temp) / "default.pptx")
            target = Path(temp) / "deck.pptx"
            tokens = load_manifest(ROOT / "slides/theme/tokens.yml")
            prep.theme_reference(base, target, tokens, footer="Chapter 9 · A Footer")
            with zipfile.ZipFile(target) as archive:
                master = archive.read("ppt/slideMasters/slideMaster1.xml").decode()
                self.assertIn('<p:hf', master)
                self.assertIn('showSpecialPlsOnTitleSld="0"', archive.read("ppt/presentation.xml").decode())
                layouts = {}
                for name in archive.namelist():
                    if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml"):
                        text = archive.read(name).decode()
                        layouts[ET.fromstring(text).find('p:cSld', NS).get('name')] = text
                self.assertIn("Chapter 9 · A Footer", layouts["Title and Content"])
                self.assertIn(tokens["colors"]["blue"], layouts["Title Slide"].split("<p:spTree>")[0])
                self.assertIn("Title Rule", layouts["Title and Content"])
                core = archive.read("docProps/core.xml").decode()
                self.assertIn("<dc:creator></dc:creator>", core)


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

    def test_pptx_checks_text_tables_notes_and_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pptx = Path(temp) / "deck.pptx"
            make_pptx(pptx)
            self.assertEqual([], verify_pptx(pptx, require_table=True, require_media=True))
            self.assertTrue(any('unintended slides' in error for error in verify_pptx(pptx, expected_slides=2)))
            make_pptx(pptx, table=False, notes="1", broken=True)
            errors = verify_pptx(pptx, require_table=True)
            self.assertTrue(any("native editable table" in error for error in errors))
            self.assertTrue(any("populated notes" in error for error in errors))
            self.assertTrue(any("broken package relationship" in error for error in errors))

    def test_site_rejects_a_deck_with_no_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, "_book/slides/chapter-07/index.html", "<html></html>")
            errors = verify_outputs(root, [], site=root / "_book")
            self.assertTrue(any("has no source: chapter-07" in error for error in errors))

    def test_site_wording_check_skips_only_the_downloads_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            listing = "<p>Instructor-Notes.zip: the instructor notes and the answer key</p>"
            write(root, "_book/front-matter/downloads.html", listing)
            write(root, "_book/chapters/01/index.html", listing)
            errors = [e for e in verify_outputs(root, [], root / "_book") if "private-material marker" in e]
            self.assertEqual(1, len(errors))
            self.assertIn("index.html", errors[0])
            self.assertNotIn("downloads", errors[0])


def stage_products(root: Path, decks=("chapter-01", "chapter-02")) -> None:
    for ext in ("pdf", "epub", "docx"):
        write(root, f"outputs/build/downloads/book-latest.{ext}", ext)
    for deck in decks:
        write(root, f"slides/_build/revealjs/{deck}/index.html", f"<html>{deck}</html>")
        write(root, f"slides/_build/pptx/{deck}/{deck}.pptx", deck)
    write(root, "slides/_build/revealjs/site_libs/revealjs/plugin/notes/speaker-view.html", "notes runtime")
    write(root, "slides/_build/revealjs/_shared/visuals/figure.svg", "<svg/>")


class BuildTests(unittest.TestCase):
    def patches(self, root: Path, run):
        return [patch.object(build_all, "source_checks", return_value=[]),
                patch.object(build_all.subprocess, "check_output", return_value="1.9.36\n"),
                patch.object(build_all, "prepare"),
                patch.object(build_all, "finish_pptx"),
                patch.object(build_all, "load_manifest", return_value={"colors": {}}),
                patch.object(build_all, "verify_outputs", return_value=[]),
                patch.object(build_all, "run", side_effect=run)]

    def test_full_build_exports_figures_first_and_renders_html_last(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for deck in ("chapter-01", "chapter-02"):
                write(root, f"slides/{deck}/index.qmd", "## Slide\n")
            calls = []

            def fake_render(workdir, command, env):
                if "scripts/export_drawio_svgs.py" in command:
                    self.assertNotIn("AA_DRAWIO_EXPORTS_READY", env)
                    calls.append("figures")
                    return
                self.assertEqual("1", env["AA_DRAWIO_EXPORTS_READY"])
                fmt = command[command.index("--to") + 1]
                calls.append(fmt)
                if "slides" in command:
                    for deck in ("chapter-01", "chapter-02"):
                        ext = "index.html" if fmt == "revealjs" else f"{deck}.pptx"
                        write(root, f"slides/_build/{fmt}/{deck}/{ext}")
                    write(root, "slides/_build/revealjs/site_libs/notes.js", "notes()")
                    return
                if (root / "_book").exists():
                    shutil.rmtree(root / "_book")
                write(root, "_book/index.html" if fmt == "html" else f"_book/Accounting-Analytics.{fmt}", fmt)
            patches = self.patches(root, fake_render)
            for p in patches: p.start()
            try:
                build_all.build(root, "fake-quarto")
            finally:
                for p in patches: p.stop()
            self.assertEqual(["figures", "pdf", "epub", "docx", "revealjs", "pptx", "html"], calls)
            for ext in ("pdf", "epub", "docx"):
                self.assertEqual(ext, (root / f"_book/downloads/book-latest.{ext}").read_text())
            self.assertTrue((root / "_book/slides/chapter-02/chapter-02.pptx").is_file())
            self.assertTrue((root / "_book/slides/site_libs/notes.js").is_file())

    def test_slides_only_exports_figures_and_skips_the_book(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root, "slides/chapter-01/index.qmd", "## Slide\n")
            commands = []
            patches = self.patches(root, lambda workdir, command, env: commands.append(command))
            for p in patches: p.start()
            try:
                with patch.object(build_all, "assemble") as assemble:
                    build_all.build(root, "fake-quarto", slides_only=True)
            finally:
                for p in patches: p.stop()
            self.assertIn("scripts/export_drawio_svgs.py", commands[0])
            self.assertEqual(["revealjs", "pptx"], [c[c.index("--to") + 1] for c in commands[1:]])
            assemble.assert_not_called()
            report = json.loads((root / "outputs/build/build-report.json").read_text())
            self.assertEqual(["chapter-01"], report["chapters"])

    def test_no_decks_renders_no_slides(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            commands = []
            patches = self.patches(root, lambda workdir, command, env: commands.append(command))
            for p in patches: p.start()
            try:
                build_all.build(root, "fake-quarto", slides_only=True)
            finally:
                for p in patches: p.stop()
            self.assertEqual(1, len(commands))

    def test_version_mismatch_stops_before_any_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(build_all, "source_checks", return_value=[]), \
                 patch.object(build_all.subprocess, "check_output", return_value="1.8.0"), \
                 patch.object(build_all, "run") as run, \
                 patch.object(build_all, "prepare") as prepare:
                with self.assertRaisesRegex(ValueError, "required"):
                    build_all.build(Path(temp), "fake-quarto")
                run.assert_not_called()
                prepare.assert_not_called()

    def test_export_failure_stops_before_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(build_all, "source_checks", return_value=[]), \
                 patch.object(build_all.subprocess, "check_output", return_value="1.9.36"), \
                 patch.object(build_all, "prepare") as prepare, \
                 patch.object(build_all, "run", side_effect=subprocess.CalledProcessError(1, "export")) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    build_all.build(Path(temp), "fake-quarto")
            self.assertEqual(1, run.call_count)
            prepare.assert_not_called()

    def test_one_deck_renders_in_isolation_and_other_outputs_survive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for deck in ("chapter-01", "chapter-02"):
                write(root, f"slides/{deck}/index.qmd", "## Slide\n")
            for fmt in ("revealjs", "pptx"):
                write(root, f"slides/_build/{fmt}/chapter-02/keep.txt", "other deck")

            def fake_render(workdir, command, env):
                if "scripts/export_drawio_svgs.py" in command:
                    return
                self.assertEqual("slides/chapter-01/index.qmd", command[2])
                relative = command[command.index("--output-dir") + 1]
                self.assertTrue(relative.startswith("_build/focused/chapter-01/"))
                write(root, f"slides/{relative}/chapter-01/index.html", "revised")
            patches = self.patches(root, fake_render)
            for p in patches: p.start()
            try:
                build_all.build(root, "quarto", slides_only=True, chapter_id="chapter-01")
            finally:
                for p in patches: p.stop()
            for fmt in ("revealjs", "pptx"):
                self.assertEqual("other deck", (root / f"slides/_build/{fmt}/chapter-02/keep.txt").read_text())
                self.assertEqual("revised", (root / f"slides/_build/{fmt}/chapter-01/index.html").read_text())
            self.assertFalse((root / "outputs/build/build-report.json").exists())

    def test_a_chapter_is_only_for_slide_builds(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            write(Path(temp), "slides/chapter-01/index.qmd", "## Slide\n")
            with self.assertRaisesRegex(ValueError, "--slides-only"):
                build_all.build(Path(temp), "quarto", chapter_id="chapter-01")
            with self.assertRaisesRegex(ValueError, "No deck for chapter-05"):
                build_all.selected_decks(Path(temp), "chapter-05")


class AssemblyTests(unittest.TestCase):
    def test_assembly_keeps_runtime_and_drops_decks_without_a_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            write(root, "_book/slides/chapter-19/index.html", "stale published artifact")
            build_all.assemble(root, ["chapter-01"])
            self.assertTrue((root / "_book/slides/site_libs/revealjs/plugin/notes/speaker-view.html").is_file())
            self.assertTrue((root / "_book/slides/_shared/visuals/figure.svg").is_file())
            self.assertTrue((root / "_book/slides/chapter-01/chapter-01.pptx").is_file())
            for deck in ("chapter-02", "chapter-19"):
                self.assertFalse((root / "_book/slides" / deck).exists(), deck)

    def test_no_decks_clears_the_published_slides(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            write(root, "_book/slides/chapter-01/index.html", "stale")
            build_all.assemble(root, [])
            self.assertFalse((root / "_book/slides").exists())
            self.assertTrue((root / "_book/downloads/book-latest.pdf").is_file())

    def test_source_files_and_nested_builds_in_the_rendered_tree_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            write(root, "slides/_build/revealjs/private.qmd", "raw authoring input")
            with self.assertRaisesRegex(ValueError, "Unexpected source"):
                build_all.assemble(root, ["chapter-01"])
            (root / "slides/_build/revealjs/private.qmd").unlink()
            write(root, "slides/_build/revealjs/_build/pptx/_shared/chart.svg", "<svg/>")
            with self.assertRaisesRegex(ValueError, "Nested build directory"):
                build_all.assemble(root, ["chapter-01"])

    def test_known_reveal_runtime_descriptor_is_packaged_but_arbitrary_yaml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage_products(root)
            write(root, "_book/index.html", "<html/>")
            relative = "chapter-01/index_files/libs/revealjs/plugin/pdf-export/plugin.yml"
            descriptor = write(root, "slides/_build/revealjs/" + relative, "name: PdfExport\nscript: pdfexport.js\n")
            write(root, "slides/_build/revealjs/" + relative.replace("plugin.yml", "pdfexport.js"), "vendor runtime")
            build_all.assemble(root, ["chapter-01"])
            self.assertTrue((root / "_book/slides" / relative).is_file())
            descriptor.write_text("name: PdfExport\nscript: pdfexport.js\nprivate: extra author content\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unexpected source"):
                build_all.assemble(root, ["chapter-01"])


class ConfigurationParsingTests(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.yml"
            path.write_text(text, encoding="utf-8")
            return load_manifest(path)

    def test_broken_json_reports_its_location(self):
        with self.assertRaisesRegex(ValueError, r"config.yml:3:3: invalid JSON: Expecting"):
            self.read('{\n  "a": 1\n  "b": 2\n}')

    def test_duplicate_keys_cannot_silently_override(self):
        for text in ('{"x": [{"k": 1, "k": 2}]}', "x:\n  - k: 1\n    k: 2\n"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "duplicate key 'k'"):
                self.read(text)

    def test_valid_json_and_yaml_load(self):
        expected = {"project": {"type": "default"}}
        self.assertEqual(expected, self.read('\ufeff{"project": {"type": "default"}}'))
        self.assertEqual(expected, self.read("project:\n  type: default\n"))
        self.assertEqual({"base": {"type": "default"}, "project": {"type": "book"}},
                         self.read("base: &base\n  type: default\nproject:\n  <<: *base\n  type: book\n"))

    def test_invalid_yaml_and_non_mapping_have_actionable_errors(self):
        with self.assertRaisesRegex(ValueError, "config.yml: invalid YAML"):
            self.read("project:\n  type: [default\n")
        with self.assertRaisesRegex(ValueError, "expected a top-level mapping"):
            self.read("[]")


if __name__ == "__main__":
    unittest.main()
