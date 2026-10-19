#!/usr/bin/env python3
"""Look at the pages of the EPUB and the DOCX that carry diagrams.

    python scripts/ebook_preview.py word outputs/build/downloads/book-latest.docx --figures 1.5 3.7 13.6
    python scripts/ebook_preview.py epub outputs/build/downloads/book-latest.epub --pages ch008 ch020
    python scripts/ebook_preview.py figures --sample 6          # the optimized PNG against the SVG, side by side

word    opens a copy of the DOCX in a hidden Word (scripts/word_check.ps1, Windows with Word), saves it as a PDF and
        renders the pages that hold the named figures with PyMuPDF; this is also the check that Word opens the file.
epub    renders chapter pages of the EPUB in headless Edge or Chrome, with the book's stylesheet, at a reading width.
figures renders a few diagrams from their SVG with rsvg-convert and puts the optimized PNG beside each, and measures how
        far the two differ (cropping or a changed layout shows as a large difference; text edges differ slightly).

Pictures go to outputs/build/ebook-preview/.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "outputs" / "build" / "ebook-preview"


def word_preview(docx: Path, figures: list[str], dpi: int = 110) -> list[Path]:
    if os.name != "nt":
        raise RuntimeError("The Word check needs Windows with Microsoft Word.")
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        raise RuntimeError("PowerShell was not found.")
    folder = "outputs/build/word-check"
    subprocess.run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts" / "word_check.ps1"),
                    "-Docx", str(docx), "-OutputDirectory", folder], check=True, cwd=ROOT)
    result = json.loads((ROOT / folder / "result.json").read_text(encoding="utf-8-sig"))
    print(f"Word {result['word_version']} opened the file: {result['pages']} pages, {result['inline_shapes']} pictures.")
    import fitz
    document = fitz.open(result["pdf"])
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for label in figures:
        needle = f"Figure {label}:"
        for number in range(document.page_count):
            page = document[number]
            if page.search_for(needle):
                target = OUT / f"word-figure-{label}.png"
                page.get_pixmap(dpi=dpi).save(target)
                written.append(target)
                print(f"  Figure {label}: page {number + 1} -> {target.relative_to(ROOT)}")
                break
        else:
            print(f"  Figure {label}: not found in the PDF Word made")
    return written


def browser() -> str:
    candidates = [shutil.which(n) for n in ("msedge", "chrome", "google-chrome", "chromium")]
    candidates += [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("Edge or Chrome was not found.")


def epub_preview(epub: Path, pages: list[str], width: int = 760, height: int = 2600) -> list[Path]:
    exe = browser()
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    with tempfile.TemporaryDirectory(prefix="epub-preview-") as temp, zipfile.ZipFile(epub) as archive:
        archive.extractall(temp)
        for name in pages:
            page = next(Path(temp).rglob(f"{name}.xhtml"), None)
            if page is None:
                print(f"  {name}: no such page")
                continue
            target = OUT / f"epub-{name}.png"
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={width},{height}",
                            f"--screenshot={target}", page.as_uri()], check=True, capture_output=True, timeout=120)
            written.append(target)
            print(f"  {name} -> {target.relative_to(ROOT)}")
    return written


def figure_comparison(sample: int, width: int = 1728) -> list[Path]:
    """Each sampled diagram: the SVG as rsvg-convert draws it, the optimized PNG, and how far they differ."""
    from PIL import Image, ImageChops, ImageDraw
    from scripts import figure_raster
    rsvg = shutil.which("rsvg-convert") or (r"C:\tools\rsvg-convert.exe" if Path(r"C:\tools\rsvg-convert.exe").is_file() else None)
    if not rsvg:
        raise RuntimeError("rsvg-convert is needed to draw the SVG for the comparison.")
    settings = figure_raster.load_settings(ROOT)
    project = figure_raster.Project(ROOT, settings)
    stems = project.discover()
    step = max(1, len(stems) // sample)
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for stem in stems[::step][:sample]:
        png = project.cache / f"{stem}.png"
        if not png.is_file():
            print(f"  {stem}: no optimized PNG yet")
            continue
        with tempfile.TemporaryDirectory() as temp:
            reference = Path(temp) / "svg.png"
            subprocess.run([rsvg, "-f", "png", "-w", str(width), "-b", "white", "-o", str(reference),
                            str(project.svg_dir / f"{stem}.svg")], check=True)
            with Image.open(reference) as a, Image.open(png) as b:
                a, b = a.convert("RGB"), b.convert("RGB")
                height = min(a.size[1], b.size[1])
                drift = abs(a.size[1] - b.size[1]) / a.size[1]
                coarse = (a.size[0] // 8, height // 8)
                difference = ImageChops.difference(a.crop((0, 0, a.size[0], height)).resize(coarse, Image.BOX),
                                                   b.crop((0, 0, b.size[0], height)).resize(coarse, Image.BOX))
                data = list(difference.convert("L").getdata())
                mean, worst = sum(data) / len(data), max(data)
                sheet = Image.new("RGB", (a.size[0], a.size[1] + b.size[1] + 40), "white")
                sheet.paste(a, (0, 20))
                sheet.paste(b, (0, a.size[1] + 40))
                draw = ImageDraw.Draw(sheet)
                draw.text((4, 4), f"{stem}: SVG drawn by rsvg-convert", fill=(200, 0, 0))
                draw.text((4, a.size[1] + 24), f"optimized PNG ({png.stat().st_size / 1e3:.0f} KB)", fill=(200, 0, 0))
                target = OUT / f"figure-{stem}.png"
                sheet.save(target)
        print(f"  {stem}: height differs {drift:.2%}; 8x8-block difference mean {mean:.2f}, worst {worst} of 255 -> "
              f"{target.relative_to(ROOT)}")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    word = sub.add_parser("word")
    word.add_argument("docx", type=Path)
    word.add_argument("--figures", nargs="+", default=["1.1", "1.5", "3.7", "13.6"], help="Figure numbers, such as 3.7.")
    epub = sub.add_parser("epub")
    epub.add_argument("epub", type=Path)
    epub.add_argument("--pages", nargs="+", default=["ch005", "ch008"], help="Page names, such as ch005.")
    epub.add_argument("--height", type=int, default=2600, help="Screenshot height in pixels (a taller window shows more).")
    epub.add_argument("--width", type=int, default=760, help="Reading width in pixels.")
    figures = sub.add_parser("figures")
    figures.add_argument("--sample", type=int, default=6)
    args = parser.parse_args(argv)
    try:
        if args.command == "word":
            word_preview(args.docx, args.figures)
        elif args.command == "epub":
            epub_preview(args.epub, args.pages, args.width, args.height)
        else:
            figure_comparison(args.sample)
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
