"""Draw the template's own marks (trim and fold marks, size labels, logo) onto the cover PDF.

IngramSpark asks that the PDF match the template's page and that everything outside its pink and blue
areas stay as the template has it, so the finished cover keeps the marks the IDML draws outside the bleed
box. The IDML's non-printing items (names ending in -np: the colored zones and the instructions) and its
barcode and QR placeholders are left out. Colors are the template's own CMYK swatches.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from scripts.print.cover_template import _apply, _matrix, _multiply

SKIP = {'BarcodeGroup', 'qrCode', 'TopLeftPlaceHolder', 'BottRightPlaceHolder', 'BackCov', 'FrontCov', 'Spine'}


def swatches(archive: zipfile.ZipFile) -> dict[str, tuple[float, float, float, float]]:
    colors = {}
    for color in ET.fromstring(archive.read('Resources/Graphic.xml')).iter('Color'):
        if color.get('Space') != 'CMYK':
            continue
        c, m, y, k = (float(v) / 100 for v in color.get('ColorValue').split())
        colors[color.get('Self')] = (c, m, y, k)
    return colors


def draw_marks(page, idml: Path) -> int:
    """Draw the template's printing marks onto a PyMuPDF page of the template's size; returns the shapes drawn."""
    import pymupdf as fitz
    with zipfile.ZipFile(idml) as archive:
        name = next(n for n in archive.namelist() if n.startswith('Spreads/Spread_'))
        spread = ET.fromstring(archive.read(name)).find('Spread')
        colors = swatches(archive)
    template_page = spread.find('Page')
    top, left, _, _ = (float(v) for v in template_page.get('GeometricBounds').split())
    page_matrix = _matrix(template_page.get('ItemTransform'))
    origin = (page_matrix[4] + left, page_matrix[5] + top)
    drawn = 0

    def shape_of(element: ET.Element, matrix: list[float]) -> None:
        nonlocal drawn
        fill = colors.get(element.get('FillColor'))
        stroke = colors.get(element.get('StrokeColor'))
        weight = float(element.get('StrokeWeight') or 0)
        if fill is None and (stroke is None or weight <= 0):
            return
        shape = page.new_shape()
        for geometry in element.iter('GeometryPathType'):
            nodes = []
            for point in geometry.find('PathPointArray').findall('PathPointType'):
                nodes.append(tuple(
                    fitz.Point(*(v - o for v, o in zip(_apply(matrix, *(float(n) for n in point.get(key).split())),
                                                       origin)))
                    for key in ('Anchor', 'LeftDirection', 'RightDirection')))
            if len(nodes) < 2:
                continue
            closed = geometry.get('PathOpen') != 'true'
            ring = nodes + ([nodes[0]] if closed else [])
            for previous, node in zip(ring, ring[1:]):
                straight = previous[0] == previous[2] and node[0] == node[1]
                if straight:
                    shape.draw_line(previous[0], node[0])
                else:
                    shape.draw_bezier(previous[0], previous[2], node[1], node[0])
        shape.finish(fill=fill if fill is not None else None, color=stroke if weight > 0 else None,
                     width=weight if weight > 0 else None, closePath=False, even_odd=True)
        shape.commit()
        drawn += 1

    def walk(node: ET.Element, matrix: list[float]) -> None:
        for child in node:
            if child.tag not in ('Rectangle', 'Polygon', 'GraphicLine', 'Oval', 'Group'):
                continue
            transform = child.get('ItemTransform')
            child_matrix = _multiply(matrix, _matrix(transform)) if transform else matrix
            if child.tag == 'Group':
                walk(child, child_matrix)
            else:
                shape_of(child, child_matrix)

    identity = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    for item in spread:
        name = item.get('Name') or ''
        if item.tag in ('Page', 'FlattenerPreference') or name.endswith('-np') or name in SKIP:
            continue
        transform = item.get('ItemTransform')
        matrix = _multiply(identity, _matrix(transform)) if transform else identity
        if item.tag == 'Group':
            walk(item, matrix)
        elif item.tag in ('Rectangle', 'Polygon', 'GraphicLine', 'Oval'):
            shape_of(item, matrix)
    return drawn
