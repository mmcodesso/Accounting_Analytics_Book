"""The ISBN barcode of the print covers: IngramSpark's own artwork, and a check that it reads.

The cover template (scripts/print/cover_template.py) carries the barcode of its ISBN as vector outlines in
a white box: IngramSpark's rules let it move inside the back cover's safe area but not change. This module
lifts those outlines out of the IDML as a Draw.io stencil (so the cover's Draw.io source shows the real
barcode and the PDF keeps it as vector paths), and decodes a rendering of the finished cover to prove that
the printed bars still read as the ISBN in the template's file name.
"""
from __future__ import annotations

import base64
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path

from scripts.print.cover_template import Box, _apply, _matrix, _multiply

# EAN-13: the first digit picks the parity pattern of the left half; L, G, R are the digit patterns.
PARITY = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL']
L_CODES = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111',
           '0001011']
R_CODES = [code.translate(str.maketrans('01', '10')) for code in L_CODES]
G_CODES = [code[::-1] for code in R_CODES]


def ean13_modules(digits: str) -> str:
    """The 95 modules of an EAN-13 as a string of 0 (space) and 1 (bar)."""
    first, left, right = int(digits[0]), digits[1:7], digits[7:13]
    text = '101'
    for digit, parity in zip(left, PARITY[first]):
        text += (L_CODES if parity == 'L' else G_CODES)[int(digit)]
    text += '01010'
    for digit in right:
        text += R_CODES[int(digit)]
    return text + '101'


def decode_ean13(modules: str) -> str | None:
    """The 13 digits of 95 modules, or None when they do not read as an EAN-13."""
    if len(modules) != 95 or modules[:3] != '101' or modules[45:50] != '01010' or modules[-3:] != '101':
        return None
    digits, parity = '', ''
    for i in range(6):
        chunk = modules[3 + 7 * i:10 + 7 * i]
        if chunk in L_CODES:
            digits, parity = digits + str(L_CODES.index(chunk)), parity + 'L'
        elif chunk in G_CODES:
            digits, parity = digits + str(G_CODES.index(chunk)), parity + 'G'
        else:
            return None
    if parity not in PARITY:
        return None
    first = str(PARITY.index(parity))
    for i in range(6):
        chunk = modules[50 + 7 * i:57 + 7 * i]
        if chunk not in R_CODES:
            return None
        digits += str(R_CODES.index(chunk))
    return first + digits


def decode_scanline(row: list[bool]) -> str | None:
    """Decode one scan line (True = dark pixel) that crosses the whole barcode, quiet zones included.

    The bars are drawn a little narrower than the modules they stand on (bar width reduction), so a
    run's width is not a whole number of modules. The 95 modules span the first bar's left edge to the
    last bar's right edge plus the reduction, which the first bar (one module wide) measures.
    """
    runs: list[tuple[bool, int]] = []
    for value in row:
        if runs and runs[-1][0] == value:
            runs[-1] = (value, runs[-1][1] + 1)
        else:
            runs.append((value, 1))
    while runs and not runs[0][0]:
        runs.pop(0)
    while runs and not runs[-1][0]:
        runs.pop()
    if len(runs) != 59:  # 30 bars and 29 spaces
        return None
    total = sum(width for _, width in runs)
    # The first bar is one module less the reduction, the space after it is one module plus the
    # reduction, so both together are two modules.
    pitch = (runs[0][1] + runs[1][1]) / 2.0
    reduction = pitch - runs[0][1]
    pitch = (total + reduction) / 95.0
    modules = ''
    for index in range(95):
        center = index * pitch + pitch / 2 - reduction / 2
        position = 0
        for value, width in runs:
            if center < position + width:
                modules += '1' if value else '0'
                break
            position += width
        else:
            modules += '0'
    return decode_ean13(modules)


@dataclass
class Barcode:
    box: Box        # the white box, in page space
    paths: list     # black outlines: ([(anchor, left, right), ...], is_open), in points from the box's corner
    isbn: str


def _outlines(shape: ET.Element, matrix: list[float], origin: tuple[float, float]) -> list:
    out = []
    for geometry in shape.iter('GeometryPathType'):
        nodes = []
        for point in geometry.find('PathPointArray').findall('PathPointType'):
            handles = []
            for key in ('Anchor', 'LeftDirection', 'RightDirection'):
                x, y = _apply(matrix, *(float(v) for v in point.get(key).split()))
                handles.append((x - origin[0], y - origin[1]))
            nodes.append(tuple(handles))
        out.append((nodes, geometry.get('PathOpen') == 'true'))
    return out


def read_barcode(idml: Path, isbn: str) -> Barcode:
    """The template's barcode: its white box and the black outlines inside it."""
    with zipfile.ZipFile(idml) as archive:
        name = next(n for n in archive.namelist() if n.startswith('Spreads/Spread_'))
        spread = ET.fromstring(archive.read(name)).find('Spread')
    page = spread.find('Page')
    top, left, _, _ = (float(v) for v in page.get('GeometricBounds').split())
    page_matrix = _matrix(page.get('ItemTransform'))
    page_origin = (page_matrix[4] + left, page_matrix[5] + top)
    group = next(item for item in spread if item.get('Name') == 'BarcodeGroup')
    identity = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    white: list = []
    black: list = []

    def walk(node: ET.Element, matrix: list[float]) -> None:
        for child in node:
            if child.tag not in ('Rectangle', 'Polygon', 'Group'):
                continue
            transform = child.get('ItemTransform')
            child_matrix = _multiply(matrix, _matrix(transform)) if transform else matrix
            if child.tag == 'Group':
                walk(child, child_matrix)
            elif child.tag == 'Rectangle':
                white.extend(_outlines(child, child_matrix, page_origin))
            else:
                black.extend(_outlines(child, child_matrix, page_origin))

    walk(group, _multiply(identity, _matrix(group.get('ItemTransform'))))
    corners = [handles[0] for nodes, _ in white for handles in nodes]
    box = Box(min(x for x, _ in corners), min(y for _, y in corners),
              max(x for x, _ in corners), max(y for _, y in corners))
    paths = [([tuple((x - box.x0, y - box.y0) for x, y in handles) for handles in nodes], is_open)
             for nodes, is_open in black]
    return Barcode(box=box, paths=paths, isbn=isbn)


def stencil_style(barcode: Barcode, unit: float = 96 / 72) -> str:
    """The Draw.io `shape=stencil(...)` of the black outlines, sized in Draw.io pixels (96 per inch)."""
    def n(value: float) -> str:
        return f'{value * unit:.3f}'.rstrip('0').rstrip('.')

    parts = []
    for nodes, is_open in barcode.paths:
        parts.append(f'<move x="{n(nodes[0][0][0])}" y="{n(nodes[0][0][1])}"/>')
        ring = nodes + ([] if is_open else [nodes[0]])
        for previous, node in zip(ring, ring[1:]):
            parts.append(f'<curve x1="{n(previous[2][0])}" y1="{n(previous[2][1])}" '
                         f'x2="{n(node[1][0])}" y2="{n(node[1][1])}" '
                         f'x3="{n(node[0][0])}" y3="{n(node[0][1])}"/>')
        if not is_open:
            parts.append('<close/>')
    xml = (f'<shape name="isbn-barcode" w="{n(barcode.box.w)}" h="{n(barcode.box.h)}" aspect="fixed" '
           f'strokewidth="inherit"><background><path>{"".join(parts)}</path><fillstroke/></background>'
           '<foreground/></shape>')
    # Draw.io's Graph.compress: percent-encode, raw deflate, base64.
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = compressor.compress(urllib.parse.quote(xml, safe="~()*!.'").encode()) + compressor.flush()
    return 'shape=stencil(' + base64.b64encode(data).decode() + ')'
