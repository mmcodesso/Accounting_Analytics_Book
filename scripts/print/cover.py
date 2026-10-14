#!/usr/bin/env python3
"""Build the print covers of the book for IngramSpark: paperback (color and black and white) and hardcover.

    python scripts/print/cover.py [--variant paperback-color|paperback-bw|hardcover ...] [--pages 798]
                                  [--template-dir DIR] [--skip-drawio] [--gs-bin PATH] [--drawio-bin PATH]

IngramSpark gives one cover template per ISBN (an InDesign IDML file named after the ISBN) whose spine
is sized for one page count. For each variant this build

1. finds the template whose ISBN is the book's (isbn.paperback-color, isbn.paperback-bw, isbn.hardcover in
   _quarto.yml) and reads its zones (scripts/print/cover_template.py);
2. paints the artwork across the whole wrap at 300 ppi (scripts/print/cover_art.py) and lays the cover out in
   Draw.io (scripts/print/cover_design.py), writing print/cover/<variant>.drawio;
3. exports the Draw.io text and barcode as a vector PDF, recolors it to CMYK, and puts it over the CMYK
   artwork on a page of the template's size, with the template's own marks (scripts/print/cover_marks.py);
4. writes PDF/X-1a:2001 with Ghostscript (scripts/print/pdfx.py) and checks the file against the template
   (the zones, the barcode, ink, fonts, color) before it is copied to outputs/print/<book name>_Cover_*.pdf
   with a JSON report and a proof image with the zones drawn on it.

With --skip-drawio the Draw.io file in print/cover is used as it is (edit it in Draw.io, then build), and
only the artwork under it is rebuilt. The words are in print/cover/cover.yml; the spine's width is the
template's, so a new page count means a new template from IngramSpark. Never part of build_all.py or the
release.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.print import cover_art, pdfx  # noqa: E402
from scripts.print.cover_barcode import decode_scanline, read_barcode  # noqa: E402
from scripts.print.cover_design import Cover  # noqa: E402
from scripts.print.cover_marks import draw_marks  # noqa: E402
from scripts.print.cover_template import PT, Box, Template, find_templates, read_template  # noqa: E402
from scripts.print.pdfops import operations  # noqa: E402
from scripts.release import read_revision  # noqa: E402

# variant -> (ISBN key in _quarto.yml, file suffix)
VARIANTS = {
    'paperback-color': ('paperback-color', 'Cover_Paperback_Color'),
    'paperback-bw': ('paperback-bw', 'Cover_Paperback_BW'),
    'hardcover': ('hardcover', 'Cover_Hardcover'),
}
TEMPLATE_DIR = ROOT / 'drafts/cover-print-template'
SOURCE_DIR = ROOT / 'print/cover'
BACKGROUND = ROOT / 'visuals/cover/background.png'
OUTPUT = ROOT / 'outputs/print'
DRAWIO_PT_PER_PX = 0.72      # Draw.io's PDF export: one pixel is 1/100 inch on the page
INK_BUILD = 220.0            # the artwork is converted to this total ink, so the JPEG's rounding stays under
INK_LIMIT = 240.0            # IngramSpark's limit
MIN_PPI = 300
ARTWORK_QUALITY = 95


# -- inputs --------------------------------------------------------------------------------------
def read_config() -> dict:
    return yaml.safe_load((ROOT / '_quarto.yml').read_text(encoding='utf-8')) or {}


def edition_label() -> str:
    book = (yaml.safe_load((ROOT / '_variables.yml').read_text(encoding='utf-8')) or {}).get('book') or {}
    return f'{str(book.get("edition", "first")).strip().title()} Edition'


def find_template(isbn: str, folder: Path) -> Path:
    digits = re.sub(r'\D', '', isbn)
    for path in find_templates(folder):
        if path.name.startswith(digits):
            return path
    raise SystemExit(f'No IngramSpark cover template for ISBN {isbn} in {folder} '
                     f'(expected {digits}-Perfect.idml or {digits}-Case.idml).')


# -- colors --------------------------------------------------------------------------------------
def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def palette_cmyk(profile: Path, colors: list[str]) -> dict[str, tuple[float, float, float, float]]:
    """CMYK fractions for each color the cover uses: paper white, 100% K black, and the rest through the
    SWOP profile (relative colorimetric)."""
    import numpy as np
    out = {}
    for color in colors:
        key = color.upper()
        if key == '#FFFFFF':
            out[key] = (0.0, 0.0, 0.0, 0.0)
        elif key == '#000000':
            out[key] = (0.0, 0.0, 0.0, 1.0)
        else:
            pixel = np.array([[hex_rgb(key)]], dtype=np.uint8)
            cmyk = cover_art.to_cmyk(pixel, profile, INK_BUILD)[0, 0] / 255.0
            out[key] = tuple(round(float(v), 4) for v in cmyk)
    return out


def number(value: float) -> str:
    text = f'{value:.4f}'.rstrip('0').rstrip('.')
    return text if text not in ('', '-0') else '0'


# -- the Draw.io export, recolored -----------------------------------------------------------------
def strip_background(drawio: Path, target: Path) -> None:
    """A copy of the Draw.io file without its background picture: the print PDF paints the artwork itself."""
    tree = ET.parse(drawio)
    for parent in tree.getroot().iter('root'):
        for cell in list(parent):
            if cell.get('id') == 'background-image':
                parent.remove(cell)
    target.parent.mkdir(parents=True, exist_ok=True)
    tree.write(target, encoding='utf-8', xml_declaration=False)


def remove_page_background(data: bytes) -> bytes:
    """Draw.io paints a white page rectangle first (the first q...Q block); the artwork must show through."""
    depth, start = 0, None
    for op in operations(data):
        if op.operator == 'q':
            if depth == 0:
                start = op.start
            depth += 1
        elif op.operator == 'Q':
            depth -= 1
            if depth == 0 and start is not None:
                block = data[start:op.end]
                if b'BT' in block or b'1 1 1 rg' not in block or b'\nf' not in block:
                    raise ValueError('The first block of the Draw.io page is not its white background')
                return data[:start] + data[op.end:]
    raise ValueError('No white page background found in the Draw.io export')


def recolor_overlay(source: Path, target: Path, cmyk: dict[str, tuple]) -> int:
    """Replace every RGB or gray operator of the Draw.io PDF with its CMYK value; returns the replacements."""
    import fitz
    doc = fitz.open(source)
    if len(doc) != 1:
        raise ValueError(f'{source.name}: expected one page, found {len(doc)}')
    count = 0
    xrefs = {xref for page in doc for xref in page.get_contents()}
    for xref in range(1, doc.xref_length()):
        if doc.xref_is_stream(xref):
            subtype = doc.xref_get_key(xref, 'Subtype')
            if subtype == ('name', '/Form'):
                xrefs.add(xref)
            elif subtype == ('name', '/Image'):
                raise ValueError(f'{source.name}: unexpected image object {xref}')
    for xref in sorted(xrefs):
        data = doc.xref_stream(xref)
        if xref in {x for page in doc for x in page.get_contents()}:
            data = remove_page_background(data)
        out, last = [], 0
        for op in operations(data):
            if op.operator in ('BI', 'sh'):
                raise ValueError(f'{source.name}: {op.operator} in object {xref}')
            if op.operator in ('rg', 'RG', 'g', 'G'):
                values = op.numbers()
                if op.operator in ('g', 'G'):
                    c = (0.0, 0.0, 0.0, 1.0 - values[0])
                else:
                    key = '#%02X%02X%02X' % tuple(round(v * 255) for v in values)
                    if key not in cmyk:
                        raise ValueError(f'{source.name}: color {key} is not in the cover palette')
                    c = cmyk[key]
                out.append(data[last:op.start])
                out.append((' '.join(number(v) for v in c) + (' K' if op.operator.isupper() else ' k')).encode())
                last = op.end
                count += 1
            elif op.operator in ('k', 'K', 'sc', 'SC', 'scn', 'SCN', 'cs', 'CS'):
                raise ValueError(f'{source.name}: unexpected color operator {op.operator} in object {xref}')
        out.append(data[last:])
        doc.update_stream(xref, b''.join(out))
    doc.save(target, garbage=3, deflate=True)
    return count


# -- the page --------------------------------------------------------------------------------------
def build_page(template: Template, idml: Path, cmyk_art_jpeg: bytes, overlay: Path, width_px: float,
               height_px: float, target: Path) -> None:
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=template.page.w, height=template.page.h)
    art = fitz.Rect(template.art.x0, template.art.y0, template.art.x1, template.art.y1)
    page.insert_image(art, stream=cmyk_art_jpeg, keep_proportion=False)
    source = fitz.open(overlay)
    clip = fitz.Rect(0, 0, width_px * DRAWIO_PT_PER_PX, height_px * DRAWIO_PT_PER_PX)
    page.show_pdf_page(art, source, 0, clip=clip)
    draw_marks(page, idml)
    doc.save(target, garbage=3, deflate=True)


# -- checks ----------------------------------------------------------------------------------------
def zone_of(template: Template, box) -> str | None:
    """The safe zone a rectangle (page points) lies inside, or None."""
    for name, zone in (('back', template.back_safe), ('spine', template.spine_safe), ('front', template.front_safe)):
        if box.x0 >= zone.x0 - 0.01 and box.x1 <= zone.x1 + 0.01 and box.y0 >= zone.y0 - 0.01 and box.y1 <= zone.y1 + 0.01:
            return name
    return None


def preflight_cover(pdf: Path, template: Template, isbn: str, pages: int, interior_pages: dict[str, int]) -> dict:
    import fitz
    import numpy as np
    problems: list[str] = []
    warnings: list[str] = []
    doc = fitz.open(pdf)
    report: dict = {'pages': len(doc)}
    if len(doc) != 1:
        problems.append(f'{len(doc)} pages (a cover is one page)')
    page = doc[0]
    report['page_in'] = [round(page.rect.width / PT, 3), round(page.rect.height / PT, 3)]
    if abs(page.rect.width - template.page.w) > 0.6 or abs(page.rect.height - template.page.h) > 0.6:
        problems.append(f'page is {report["page_in"]} in, the template says '
                        f'{round(template.page.w / PT, 3)} x {round(template.page.h / PT, 3)}')
    # fonts
    fonts = doc.get_page_fonts(0)
    report['fonts'] = sorted({f[3].split('+')[-1] for f in fonts})
    for font in fonts:
        if font[2] == 'Type3':
            problems.append(f'Type 3 font {font[3]}')
        if '+' not in font[3]:
            problems.append(f'font {font[3]} is not embedded')
    # color: nothing but CMYK
    for xref in range(1, doc.xref_length()):
        text = doc.xref_object(xref, compressed=True)
        if '/DeviceRGB' in text or '/CalRGB' in text:
            if '/OutputIntent' not in text:
                problems.append(f'RGB color space in object {xref}')
        for key in ('/SMask', '/BM', '/ca', '/CA'):
            for match in re.finditer(re.escape(key) + r'(?![\w])\s*(/?[\w.]+)', text):
                value = match.group(1)
                opaque = (value == '/None' if key == '/SMask' else value in ('/Normal', '/Compatible') if key == '/BM'
                          else float(value) >= 1)
                if not opaque:
                    problems.append(f'transparency in object {xref} ({key} {value})')
    for xref in {x for x in page.get_contents()} | {i[0] for i in page.get_xobjects()}:
        if doc.xref_is_stream(xref) and doc.xref_get_key(xref, 'Subtype')[1] != '/Image':
            for op in operations(doc.xref_stream(xref)):
                if op.operator in ('rg', 'RG'):
                    problems.append(f'RGB operator {op.operator} in object {xref}')
                    break
    # images
    images = page.get_image_info(xrefs=True)
    report['images'] = []
    for image in images:
        bbox = fitz.Rect(image['bbox'])
        ppi = image['width'] / (bbox.width / PT)
        info = {'pixels': [image['width'], image['height']], 'cs': image['colorspace'], 'ppi': round(ppi)}
        report['images'].append(info)
        if image['colorspace'] != 4:
            problems.append(f'image is not CMYK ({image["colorspace"]} components)')
        if ppi < MIN_PPI - 1:
            problems.append(f'image resolution is {ppi:.0f} ppi (IngramSpark wants {MIN_PPI})')
    # PDF/X
    catalog = doc.xref_object(doc.pdf_catalog(), compressed=True)
    report['output_intent'] = '/OutputIntents' in catalog
    if '/OutputIntents' not in catalog:
        problems.append('no output intent')
    metadata = doc.xref_get_key(-1, 'Info')
    info_xref = int(metadata[1].split()[0]) if metadata[0] == 'xref' else None
    pdfx_version = doc.xref_get_key(info_xref, 'GTS_PDFXVersion')[1] if info_xref else ''
    report['pdfx'] = pdfx_version
    if 'PDF/X-1a' not in pdfx_version:
        problems.append(f'not PDF/X-1a ({pdfx_version!r})')
    # ink: render the CMYK page and take the heaviest pixel
    pixmap = page.get_pixmap(dpi=100, colorspace=fitz.csCMYK)
    samples = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 4)
    total = samples.astype(np.float32).sum(axis=2) / 255.0 * 100.0
    inside = total[int(template.art.y0 / PT * 100):int(template.art.y1 / PT * 100) + 1,
                   int(template.art.x0 / PT * 100):int(template.art.x1 / PT * 100) + 1]
    report['max_total_ink'] = round(float(inside.max()), 1)
    if inside.max() > INK_LIMIT:
        problems.append(f'total ink {inside.max():.0f}% (limit {INK_LIMIT:.0f}%)')
    # text stays in the pink areas, and no two lines of text touch
    spans = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                if span['text'].strip():
                    spans.append((fitz.Rect(span['bbox']), span['text']))
    report['text_spans'] = len(spans)
    for box, text in spans:
        if zone_of(template, box) is None:
            problems.append(f'text outside the safe areas: {text[:40]!r} at {[round(v / PT, 2) for v in box]}')
        elif zone_of(template, box) == 'spine' and (box.x0 < template.spine.x0 + 0.2 * PT
                                                    or box.x1 > template.spine.x1 - 0.2 * PT):
            warnings.append(f'spine text within 0.2 in of a fold: {text[:30]!r}')
    def core(box):  # a span's box is the font's full ascent and descent: compare the middle of each line
        trim = box.height * 0.2
        return fitz.Rect(box.x0, box.y0 + trim, box.x1, box.y1 - trim)

    for i, (a, ta) in enumerate(spans):
        for b, tb in spans[i + 1:]:
            overlap = core(a) & core(b)
            if not overlap.is_empty and overlap.width > 0.5 and overlap.height > 0.5:
                problems.append(f'text overlaps text: {ta[:25]!r} and {tb[:25]!r}')
    # the barcode: inside the safe area, white box, and it reads as the ISBN
    barcode = read_barcode(Path(template.path), isbn).box
    if zone_of(template, fitz.Rect(barcode.x0, barcode.y0, barcode.x1, barcode.y1)) != 'back':
        problems.append('barcode is outside the back cover\'s safe area')
    clip = fitz.Rect(barcode.x0 + 4, barcode.y0 + 0.30 * barcode.h, barcode.x1 - 4, barcode.y0 + 0.62 * barcode.h)
    scan = page.get_pixmap(dpi=1200, clip=clip, colorspace=fitz.csGRAY)
    gray = np.frombuffer(scan.samples, dtype=np.uint8).reshape(scan.height, scan.width)
    decoded = {decode_scanline((gray[y] < 128).tolist()) for y in range(5, scan.height, 40)}
    report['barcode'] = sorted(str(d) for d in decoded)
    if decoded != {isbn}:
        problems.append(f'barcode reads {sorted(map(str, decoded))}, the ISBN is {isbn}')
    # the bleed is covered: no white along the edges of the art box
    scale = 100 / PT
    rgb = page.get_pixmap(dpi=100, colorspace=fitz.csRGB)
    pixels = np.frombuffer(rgb.samples, dtype=np.uint8).reshape(rgb.height, rgb.width, 3)
    x0, y0 = max(int(template.art.x0 * scale) + 1, 0), max(int(template.art.y0 * scale) + 1, 0)
    x1, y1 = int(template.art.x1 * scale) - 1, int(template.art.y1 * scale) - 1
    edges = [pixels[y0:y1, x0:x0 + 8], pixels[y0:y1, x1 - 8:x1], pixels[y0:y0 + 8, x0:x1], pixels[y1 - 8:y1, x0:x1]]
    if any((edge > 250).all(axis=2).any() for edge in edges):
        problems.append('white along an edge of the bleed box')
    # the spine against the page count
    report['spine_in'] = round(template.spine_width_in, 3)
    for name, count in interior_pages.items():
        if count != pages:
            warnings.append(f'{name} has {count} pages, the template\'s spine is for {pages}: ask IngramSpark for a new '
                            'template and rebuild')
    report['problems'] = problems
    report['warnings'] = warnings
    report['ok'] = not problems
    return report


def proof_image(pdf: Path, template: Template, target: Path, gs: str, dpi: int = 110) -> None:
    """The cover as Ghostscript renders it through the SWOP profile, with the template's zones drawn on it:
    bleed (cyan), trim and folds (green and yellow), safe areas (magenta)."""
    import subprocess
    from PIL import Image, ImageDraw
    target.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([gs, '-dBATCH', '-dNOPAUSE', '-dQUIET', '-sDEVICE=png16m', f'-r{dpi}',
                             f'-sOutputFile={target}', str(pdf)], capture_output=True, text=True)
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError(f'Ghostscript could not render the proof: {result.stdout}{result.stderr}')
    image = Image.open(target).convert('RGB')
    draw = ImageDraw.Draw(image)
    scale = dpi / PT
    zones = [(template.art, (0, 174, 239)), (template.back, (0, 180, 0)), (template.spine, (230, 200, 0)),
             (template.front, (0, 180, 0)), (template.back_safe, (225, 50, 150)),
             (template.spine_safe, (225, 50, 150)), (template.front_safe, (225, 50, 150))]
    for box, color in zones:
        draw.rectangle([box.x0 * scale, box.y0 * scale, box.x1 * scale, box.y1 * scale], outline=color, width=1)
    image.save(target)


# -- build -----------------------------------------------------------------------------------------
def build_variant(variant: str, args, config: dict, copy: dict, gs: str, drawio_bin: Path, book_name: str,
                  interior_pages: dict[str, int]) -> dict:
    import fitz
    key, suffix = VARIANTS[variant]
    isbn_text = str((config.get('isbn') or {}).get(key) or '').strip()
    if not isbn_text:
        raise SystemExit(f'isbn.{key} is blank in _quarto.yml.')
    isbn = re.sub(r'\D', '', isbn_text)
    idml = find_template(isbn, Path(args.template_dir))
    template = read_template(idml)
    if template.isbn != isbn:
        raise SystemExit(f'{idml.name} is the template of {template.isbn}, not of ISBN {isbn_text}.')
    started = time.time()
    work = OUTPUT / 'work' / 'cover' / variant
    work.mkdir(parents=True, exist_ok=True)
    profile = cover_art.cmyk_profile_path(gs)
    barcode = read_barcode(idml, isbn)

    # artwork across the wrap
    art = cover_art.compose(template, BACKGROUND)
    # the author's note and the footer sit on the dotted surface: dim it there so the small type reads
    scrim = Box(template.back.x0 + 0.1 * PT, template.back.y0 + 570, template.barcode.x0 - 0.1 * PT, template.back.y1 + 8)
    cover_art.darken(art, scrim, 0.62, feather_in=0.5)
    drawio = SOURCE_DIR / f'{variant}.drawio'
    if not args.skip_drawio or not drawio.is_file():
        design = Cover(template, copy, edition_label(), barcode, cover_art.proxy_jpeg(art))
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        drawio.write_text(design.build(), encoding='utf-8')
        width_px, height_px = design.width, design.height
    else:
        root = ET.parse(drawio).getroot().find('.//mxGraphModel')
        width_px, height_px = float(root.get('pageWidth')), float(root.get('pageHeight'))
    cmyk = cover_art.to_cmyk(cover_art.with_noise(art.rgb), profile, INK_BUILD)
    artwork_jpeg = cover_art.cmyk_jpeg_bytes(cmyk, ARTWORK_QUALITY, art.ppi)
    ink = cover_art.max_total_ink(cmyk)
    ink_jpeg = cover_art.max_total_ink(cover_art.decode_cmyk_jpeg(artwork_jpeg))  # what the printer decodes

    # text, rules and barcode from Draw.io
    from scripts.export_drawio_svgs import export_pdf
    overlay_source = work / 'overlay-source.drawio'
    strip_background(drawio, overlay_source)
    export_pdf(drawio_bin, overlay_source, work / 'overlay-rgb.pdf', crop=False)
    palette = palette_cmyk(profile, ['#FFFFFF', '#E3A93B', '#000000'])
    replaced = recolor_overlay(work / 'overlay-rgb.pdf', work / 'overlay-cmyk.pdf', palette)

    flat = work / 'cover-flat.pdf'
    build_page(template, idml, artwork_jpeg, work / 'overlay-cmyk.pdf', width_px, height_px, flat)
    clean = work / 'cover-clean.pdf'
    pdfx.strip_transparency_groups(flat, clean)
    final = work / 'cover-pdfx.pdf'
    pdfx.to_pdfx(clean, final, f'Accounting Analytics: An Integrated Approach ({edition_label()}, cover)', gs, work)

    report = preflight_cover(final, template, isbn, args.pages, interior_pages)
    if ink_jpeg > INK_LIMIT:
        report['problems'].append(f'artwork ink after JPEG compression reaches {ink_jpeg:.0f}% (limit {INK_LIMIT:.0f}%)')
        report['ok'] = False
    report.update({
        'variant': variant, 'isbn': isbn_text, 'template': idml.name, 'kind': template.kind,
        'trim_in': template.trim_in, 'spine_in': round(template.spine_width_in, 3), 'template_pages': args.pages,
        'artwork_ink_max': round(ink, 1), 'artwork_ink_max_decoded': round(ink_jpeg, 1), 'recolored': replaced, 'ghostscript': gs,
        'seconds': round(time.time() - started), 'drawio': str(drawio.relative_to(ROOT)),
    })
    name = f'{book_name}_{suffix}'
    destination = OUTPUT / f'{name}.pdf'
    proof_image(final, template, OUTPUT / f'{name}_proof.png', gs)
    (OUTPUT / f'{name}.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if report['ok']:
        shutil.copy2(final, destination)
        report['output'] = str(destination.relative_to(ROOT))
    return report


def summary(report: dict) -> str:
    lines = [f'{report["variant"]}: ' + ('OK' if report['ok'] else 'FAILED') +
             f' ({report["template"]}, spine {report["spine_in"]} in, page {report["page_in"][0]} x {report["page_in"][1]} in,'
             f' ink {report["max_total_ink"]}%, barcode {", ".join(report["barcode"])})']
    lines += [f'  problem: {p}' for p in report['problems']]
    lines += [f'  warning: {w}' for w in report['warnings']]
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--variant', action='append', choices=sorted(VARIANTS), help='Default: all three.')
    parser.add_argument('--pages', type=int, default=798, help='The page count the templates were made for (798).')
    parser.add_argument('--template-dir', default=str(TEMPLATE_DIR), help='Folder with the IngramSpark IDML templates.')
    parser.add_argument('--skip-drawio', action='store_true', help='Use print/cover/<variant>.drawio as it is.')
    parser.add_argument('--gs-bin', help='Path to gswin64c.exe (or set GS_BIN).')
    parser.add_argument('--drawio-bin', type=Path, help='Path to draw.io (or set DRAWIO_BIN).')
    args = parser.parse_args()
    from scripts.export_drawio_svgs import find_drawio_executable
    gs = pdfx.find_ghostscript(args.gs_bin)
    drawio_bin = find_drawio_executable(args.drawio_bin)
    config = read_config()
    copy = yaml.safe_load((SOURCE_DIR / 'cover.yml').read_text(encoding='utf-8'))
    book_name = read_revision(ROOT).book_name
    import fitz
    interior_pages = {}
    for suffix in ('Print_Color', 'Print_BW'):
        interior = OUTPUT / f'{book_name}_{suffix}.pdf'
        if interior.is_file():
            interior_pages[interior.name] = len(fitz.open(interior))
    failed = []
    for variant in args.variant or list(VARIANTS):
        report = build_variant(variant, args, config, copy, gs, drawio_bin, book_name, interior_pages)
        print(summary(report), flush=True)
        if not report['ok']:
            failed.append(variant)
    if failed:
        print('Preflight failed: ' + ', '.join(failed), flush=True)
        return 1
    print('Covers built. Upload each to IngramSpark with its interior, read its error report, and order a proof.',
          flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
