"""filters/epub-markup.lua: the EPUB loses the alt attribute on figure wrappers (EPUBCheck RSC-005), nothing else changes."""
from __future__ import annotations

import io
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "filters" / "epub-markup.lua"


def find_pandoc() -> str | None:
    found = shutil.which("pandoc")
    if found:
        return found
    quarto = shutil.which("quarto")
    if quarto:
        for candidate in (Path(quarto).resolve().parent / "tools").rglob("pandoc*"):
            if candidate.name in ("pandoc", "pandoc.exe"):
                return str(candidate)
    return None


def png() -> bytes:
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, "PNG")
    return buffer.getvalue()


SOURCE = ('::: {.quarto-float alt="WRAPPER-ALT"}\n'
          '![A caption.](pixel.png){alt="IMAGE-ALT"}\n\n'
          'Some [text]{alt="SPAN-ALT"} here.\n'
          ':::\n')


@unittest.skipUnless(find_pandoc(), "Pandoc is not installed")
class EpubMarkupTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="epub markup ")
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        (self.dir / "pixel.png").write_bytes(png())
        (self.dir / "a.md").write_text(SOURCE, encoding="utf-8")

    def convert(self, target: str, output: str, *, filtered: bool = True) -> Path:
        command = [find_pandoc(), "a.md", "-t", target, "-o", output]
        if filtered:
            command += ["--lua-filter", str(FILTER)]
        done = subprocess.run(command, cwd=self.dir, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return self.dir / output

    def page(self, epub: Path) -> str:
        with zipfile.ZipFile(epub) as archive:
            for name in archive.namelist():
                if name.endswith(".xhtml"):
                    text = archive.read(name).decode("utf-8")
                    if "quarto-float" in text:
                        return text
        self.fail("no page with the figure")

    def test_without_the_filter_the_attributes_are_there(self) -> None:
        text = self.page(self.convert("epub3", "plain.epub", filtered=False))
        self.assertIn('alt="WRAPPER-ALT"', text)
        self.assertIn('alt="SPAN-ALT"', text)

    def test_the_wrapper_and_span_lose_alt_and_the_image_keeps_it(self) -> None:
        text = self.page(self.convert("epub3", "filtered.epub"))
        self.assertNotIn("WRAPPER-ALT", text)
        self.assertNotIn("SPAN-ALT", text)
        self.assertRegex(text, r'<img [^>]*alt="IMAGE-ALT"')
        self.assertEqual(re.findall(r"<div[^>]*>", text), ['<div class="quarto-float">'])

    def test_html_is_left_alone(self) -> None:
        done = subprocess.run([find_pandoc(), "a.md", "-t", "html", "--lua-filter", str(FILTER)], cwd=self.dir,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('alt="WRAPPER-ALT"', done.stdout)

    def test_docx_is_left_alone(self) -> None:
        output = self.convert("docx", "a.docx")
        self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
