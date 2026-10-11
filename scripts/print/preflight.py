"""Check a print interior against IngramSpark's file requirements.

    python scripts/print/preflight.py FILE --mode cmyk|gray [--stage latex|final] [--draft] [--json OUT]

IngramSpark's File Creation Guide (8.24.26) asks for single pages at the exact trim size, a 0.5in
margin on every side plus 0.125in of no ink at the spine, embedded fonts, no transparency, rules of at
least 0.125pt, grayscale for black-and-white interiors and CMYK of at most 240% total ink for color
ones, an even page count, and PDF/X-1a:2001 or PDF/X-3:2002. scripts/print/build.py runs the checks
twice: on the LaTeX output once its transparency groups are removed (stage latex: everything but the
annotations, which the PDF/X conversion removes, and the PDF/X keys), and on the PDF/X file (stage
final). A failed check exits with status 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.print import palette  # noqa: E402
from scripts.print.pdfops import operations  # noqa: E402

PT = 72.0
TRIM = (612.0, 792.0)        # US Letter, no bleed
SAFE = 0.5 * PT              # from every trim edge
SAFE_SPINE = 0.625 * PT      # 0.5in plus the 0.125in no-ink strip at the spine
MIN_RULE = 0.125             # pt
SLIDE_TEXT = ('Chapter slides', 'Case slides', 'View slides', 'Download PowerPoint')
TOLERANCE = 0.5              # pt, for measured positions


class Check:
    def __init__(self, name: str, description: str):
        self.name, self.description = name, description
        self.problems: list[str] = []
        self.info: dict = {}

    def fail(self, message: str, limit: int = 25) -> None:
        if len(self.problems) < limit:
            self.problems.append(message)
        elif len(self.problems) == limit:
            self.problems.append('… more of the same')

    @property
    def ok(self) -> bool:
        return not self.problems

    def report(self) -> dict:
        return {'ok': self.ok, 'description': self.description, 'problems': self.problems, **self.info}


def content_streams(doc: fitz.Document) -> list[tuple[int, str]]:
    """(xref, where) for every page content stream, form XObject and Type 3 glyph procedure."""
    streams = []
    for page in doc:
        streams += [(xref, f'page {page.number + 1}') for xref in page.get_contents()]
    for xref in range(1, doc.xref_length()):
        if not doc.xref_is_stream(xref):
            continue
        if doc.xref_get_key(xref, 'Subtype') == ('name', '/Form'):
            streams.append((xref, f'form {xref}'))
    for xref in range(1, doc.xref_length()):
        procs = doc.xref_get_key(xref, 'CharProcs')
        if procs[0] == 'dict':
            streams += [(int(ref), f'Type 3 glyph {ref}') for ref in re.findall(r'(\d+) 0 R', procs[1])]
    return streams


def check_pages(doc: fitz.Document) -> Check:
    check = Check('pages', 'every page is 8.5 x 11 in (612 x 792 pt), and the page count is even')
    for page in doc:
        width, height = page.mediabox.width, page.mediabox.height
        if abs(width - TRIM[0]) > 0.01 or abs(height - TRIM[1]) > 0.01:
            check.fail(f'page {page.number + 1} is {width:.2f} x {height:.2f} pt')
    if doc.page_count % 2:
        check.fail(f'{doc.page_count} pages: the count must be even')
    check.info['pages'] = doc.page_count
    return check


def check_front_matter(doc: fitz.Document) -> Check:
    check = Check('front matter', 'page 1 is the title page and page 2 the copyright page (no cover)')
    first, second = doc[0], doc[1]
    if 'Accounting Analytics' not in first.get_text() or first.get_images():
        check.fail('page 1 is not the text title page')
    if 'Copyright' not in second.get_text():
        check.fail('page 2 is not the copyright page')
    return check


def check_annotations(doc: fitz.Document) -> Check:
    check = Check('annotations', 'no annotations or links (PDF/X allows none on the page)')
    count = 0
    for page in doc:
        annots = doc.xref_get_key(page.xref, 'Annots')
        if annots[0] != 'null':
            count += 1
            check.fail(f'page {page.number + 1} has annotations')
    check.info['pages_with_annotations'] = count
    return check


def check_fonts(doc: fitz.Document) -> Check:
    check = Check('fonts', 'every font is embedded, and none is a Type 3 font')
    fonts = {}
    for page in doc:
        for xref, ext, kind, basefont, *_ in page.get_fonts(full=True):
            fonts[xref] = (ext, kind, basefont)
    for xref, (ext, kind, basefont) in sorted(fonts.items()):
        if kind == 'Type3':
            check.fail(f'Type 3 font {basefont or xref}')
        elif ext == 'n/a':
            check.fail(f'font {basefont} ({kind}) is not embedded')
    check.info['fonts'] = len(fonts)
    return check


def check_transparency(doc: fitz.Document) -> Check:
    check = Check('transparency', 'no opacity below 1, soft mask, blend mode or transparency group')
    for xref in range(1, doc.xref_length()):
        text = doc.xref_object(xref, compressed=True)
        for key, value in re.findall(r'/(SMask|BM|ca|CA)(?!\w)\s*(/?[\w.]+)', text):
            if key == 'SMask' and value != '/None':
                check.fail(f'object {xref}: soft mask')
            elif key == 'BM' and value not in ('/Normal', '/Compatible'):
                check.fail(f'object {xref}: blend mode {value}')
            elif key in ('ca', 'CA') and not value.startswith('/') and float(value) < 1:
                check.fail(f'object {xref}: opacity {value}')
        if re.search(r'/Group\s*<<[^>]*/S\s*/Transparency', text):
            check.fail(f'object {xref}: transparency group')
        group = doc.xref_get_key(xref, 'Group')
        if group[0] == 'xref' and '/Transparency' in doc.xref_object(int(group[1].split()[0]), compressed=True):
            check.fail(f'object {xref}: transparency group')
    return check


def check_color(doc: fitz.Document, mode: str) -> tuple[Check, Check]:
    allowed = {'g', 'G'} if mode == 'gray' else {'g', 'G', 'k', 'K'}
    color = Check('color', 'only gray operators' if mode == 'gray'
                  else 'only CMYK and gray operators (no RGB, no other color spaces)')
    ink = Check('total ink', f'no CMYK color above {palette.MAX_TOTAL_INK}% total ink')
    used = Counter()
    max_ink = 0.0
    for xref, where in content_streams(doc):
        for op in operations(doc.xref_stream(xref)):
            if op.operator in ('rg', 'RG', 'sc', 'SC', 'scn', 'SCN', 'cs', 'CS') or (
                    op.operator in ('g', 'G', 'k', 'K') and op.operator not in allowed):
                color.fail(f'{where}: {b" ".join(op.operands).decode("latin-1")} {op.operator}')
            elif op.operator in ('k', 'K'):
                values = op.numbers() or []
                total = sum(values) * 100
                max_ink = max(max_ink, total)
                used[' '.join(f'{v:g}' for v in values)] += 1
                if total > palette.MAX_TOTAL_INK + 0.5:
                    ink.fail(f'{where}: {total:.0f}% ({" ".join(f"{v:g}" for v in values)})')
            elif op.operator == 'BI':
                color.fail(f'{where}: inline image')
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, 'Subtype') == ('name', '/Image'):
            space = doc.xref_get_key(xref, 'ColorSpace')[1]
            if space not in (('/DeviceGray',) if mode == 'gray' else ('/DeviceGray', '/DeviceCMYK')):
                color.fail(f'image {xref} in {space}')
    ink.info['max_total_ink'] = round(max_ink, 1)
    color.info['cmyk_colors'] = len(used)
    return color, ink


def check_rich_black_text(doc: fitz.Document, mode: str) -> Check:
    check = Check('black text', 'dark text is black ink alone (no rich black), as IngramSpark advises')
    if mode == 'gray':
        check.info['note'] = 'gray interior: every color is a gray'
        return check
    for page in doc:
        for span in page.get_texttrace():
            values = span.get('color') or ()
            if len(values) == 4 and values[3] >= 0.8 and sum(values[:3]) > 0.01:
                check.fail(f'page {page.number + 1}: text in {values}')
                break
    return check


def check_safe_area(doc: fitz.Document) -> Check:
    check = Check('safe area', 'text and drawings stay 0.5in from the trim, 0.625in from the spine')
    worst = {'outer': 99.0, 'spine': 99.0, 'top': 99.0, 'bottom': 99.0}
    for page in doc:
        recto = page.number % 2 == 0  # page 1 is a right-hand page: its spine is on the left
        boxes = [fitz.Rect(span['bbox']) for block in page.get_text('dict')['blocks']
                 for line in block.get('lines', []) for span in line['spans'] if span['text'].strip()]
        for drawing in page.get_drawings():
            invisible = drawing.get('color') is None and drawing.get('fill') in (None, (1.0,), (1.0, 1.0, 1.0),
                                                                                    (0.0, 0.0, 0.0, 0.0))
            if not invisible:
                boxes.append(fitz.Rect(drawing['rect']))
        boxes += [fitz.Rect(info['bbox']) for info in page.get_image_info()]
        for box in boxes:
            if box.is_empty and box.width == 0 and box.height == 0:
                continue
            left, right = box.x0, TRIM[0] - box.x1
            spine, outer = (left, right) if recto else (right, left)
            distances = {'outer': outer, 'spine': spine, 'top': box.y0, 'bottom': TRIM[1] - box.y1}
            for side, distance in distances.items():
                worst[side] = min(worst[side], distance)
                limit = SAFE_SPINE if side == 'spine' else SAFE
                if distance < limit - TOLERANCE:
                    check.fail(f'page {page.number + 1}: {distance / PT:.3f}in from the {side} edge')
    check.info['closest_in'] = {side: round(value / PT, 3) for side, value in worst.items()}
    return check


def check_rules(doc: fitz.Document) -> Check:
    check = Check('rules', f'every stroked line is at least {MIN_RULE}pt wide')
    thinnest = 99.0
    for page in doc:
        for drawing in page.get_drawings():
            if drawing.get('color') is None or drawing.get('width') is None:
                continue
            width = drawing['width']
            thinnest = min(thinnest, width)
            if width < MIN_RULE:
                check.fail(f'page {page.number + 1}: line of {width:.3f}pt')
    check.info['thinnest_pt'] = round(thinnest, 3)
    return check


def check_text(doc: fitz.Document, draft: bool) -> Check:
    check = Check('print text', 'no slide links in the chapters' + ('' if draft else ', and no unassigned ISBN'))
    forbidden = SLIDE_TEXT + (() if draft else ('ISBN to be assigned',))
    for page in doc:
        text = page.get_text()
        for phrase in forbidden:
            if phrase in text:
                check.fail(f'page {page.number + 1}: "{phrase}"')
    return check


def check_pdfx(doc: fitz.Document) -> Check:
    check = Check('PDF/X', 'GTS_PDFXVersion, an output intent, and a TrimBox on every page; not encrypted')
    info = doc.xref_get_key(-1, 'Info')
    version = None
    if info[0] == 'xref':
        found = doc.xref_get_key(int(info[1].split()[0]), 'GTS_PDFXVersion')
        version = found[1] if found[0] == 'string' else None
    if not version:
        check.fail('no GTS_PDFXVersion in the document information')
    if doc.xref_get_key(doc.pdf_catalog(), 'OutputIntents')[0] == 'null':
        check.fail('no output intent')
    for page in doc:
        if doc.xref_get_key(page.xref, 'TrimBox')[0] == 'null' and doc.xref_get_key(page.xref, 'ArtBox')[0] == 'null':
            check.fail(f'page {page.number + 1} has no TrimBox')
    if doc.is_encrypted or doc.needs_pass:
        check.fail('the file is encrypted')
    check.info['version'] = version
    return check


def preflight(path: Path, mode: str, stage: str = 'final', draft: bool = False) -> dict:
    doc = fitz.open(path)
    checks = [check_pages(doc), check_front_matter(doc), check_fonts(doc), check_transparency(doc),
              *check_color(doc, mode), check_rich_black_text(doc, mode), check_safe_area(doc), check_rules(doc),
              check_text(doc, draft)]
    if stage == 'final':
        checks += [check_annotations(doc), check_pdfx(doc)]
    data = path.read_bytes()
    return {
        'file': str(path), 'mode': mode, 'stage': stage, 'pages': doc.page_count, 'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(), 'ok': all(check.ok for check in checks),
        'checks': {check.name: check.report() for check in checks},
    }


def summary(report: dict) -> str:
    lines = [f'{report["file"]}: {report["pages"]} pages, {report["bytes"] / 1e6:.1f} MB '
             f'({report["mode"]}, {report["stage"]})']
    for name, check in report['checks'].items():
        extra = {key: value for key, value in check.items() if key not in ('ok', 'description', 'problems')}
        lines.append(f'  {"ok  " if check["ok"] else "FAIL"} {name}: {check["description"]}'
                     + (f' {extra}' if extra else ''))
        lines += [f'         {problem}' for problem in check['problems']]
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('file', type=Path)
    parser.add_argument('--mode', choices=('cmyk', 'gray'), required=True)
    parser.add_argument('--stage', choices=('latex', 'final'), default='final')
    parser.add_argument('--draft', action='store_true', help='Allow "ISBN to be assigned".')
    parser.add_argument('--json', type=Path, help='Write the report as JSON.')
    args = parser.parse_args()
    report = preflight(args.file, args.mode, args.stage, args.draft)
    print(summary(report))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
