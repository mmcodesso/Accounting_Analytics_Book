"""Read IngramSpark's cover template (the InDesign IDML file) for the print covers.

IngramSpark makes one template per ISBN: the file name starts with the ISBN-13 (9786597822140-Perfect.idml)
and its page count fixes the spine. The template draws its zones as guides (GuideBackLeftTrim,
GuideSpineLeftSafety, ...) and as labeled shapes (BackCov, Spine, FrontCov, BarcodeGroup); its text is
outlined, so the page count is not in the file and comes from the command line (scripts/print/cover.py).

Everything is returned in page space: points from the left and the top of the template's page, the
coordinate system the final PDF uses. `scripts/print/cover.py` builds the artwork from `Template.art` and
the zones, and places it on a page of `Template.page` points.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

ISBN_IN_NAME = re.compile(r'^(97[89]\d{10})-(Perfect|Case)', re.IGNORECASE)
PT = 72.0


@dataclass
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    def inches(self) -> tuple[float, float, float, float]:
        return tuple(round(v / PT, 4) for v in (self.x0, self.y0, self.x1, self.y1))


@dataclass
class Template:
    path: Path
    isbn: str                       # ISBN-13 digits, from the file name
    kind: str                       # 'perfect' (paperback) or 'case' (hardcover case laminate)
    page: Box                       # the template's page: the size of the PDF IngramSpark wants
    art: Box                        # the bleed box: the artwork must cover all of it
    back: Box                       # the visible back face (inside the trim, or the board)
    spine: Box                      # the spine (between its fold lines)
    front: Box                      # the visible front face
    back_safe: Box                  # the pink areas: text and anything important stays inside
    spine_safe: Box
    front_safe: Box
    barcode: Box                    # the template's white barcode box
    guides: dict[str, float] = field(default_factory=dict)
    shapes: dict[str, Box] = field(default_factory=dict)

    @property
    def spine_width_in(self) -> float:
        return self.spine.w / PT

    @property
    def trim_in(self) -> tuple[float, float]:
        return (round(self.front.w / PT, 3), round(self.front.h / PT, 3))


def isbn13_valid(digits: str) -> bool:
    if not re.fullmatch(r'\d{13}', digits):
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
    return (10 - total % 10) % 10 == int(digits[12])


def _matrix(text: str) -> list[float]:
    return [float(v) for v in text.split()]


def _multiply(parent: list[float], child: list[float]) -> list[float]:
    """IDML's [a b c d tx ty] row-vector transforms: the child's, then the parent's."""
    a, b, c, d, e, f = parent
    A, B, C, D, E, F = child
    return [A * a + B * c, A * b + B * d, C * a + D * c, C * b + D * d, E * a + F * c + e, E * b + F * d + f]


def _apply(m: list[float], x: float, y: float) -> tuple[float, float]:
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


def _shape_box(element: ET.Element, parent: list[float]) -> Box | None:
    """The bounding box, in spread coordinates, of every path anchor under the element."""
    xs: list[float] = []
    ys: list[float] = []

    def walk(node: ET.Element, matrix: list[float]) -> None:
        transform = node.get('ItemTransform')
        matrix = _multiply(matrix, _matrix(transform)) if transform else matrix
        for child in node:
            if child.tag == 'Properties':
                geometry = child.find('PathGeometry')
                if geometry is not None:
                    for point in geometry.iter('PathPointType'):
                        x, y = (float(v) for v in point.get('Anchor').split())
                        px, py = _apply(matrix, x, y)
                        xs.append(px)
                        ys.append(py)
            elif child.tag in ('Rectangle', 'Group', 'GraphicLine', 'Oval', 'Polygon', 'TextFrame'):
                walk(child, matrix)

    walk(element, parent)
    return Box(min(xs), min(ys), max(xs), max(ys)) if xs else None


def read_template(path: Path) -> Template:
    path = Path(path)
    match = ISBN_IN_NAME.match(path.name)
    if not match:
        raise ValueError(f'{path.name}: the template file name must start with the ISBN-13 and its type '
                         '(for example 9786597822140-Perfect.idml)')
    isbn, kind = match.group(1), match.group(2).lower()
    if not isbn13_valid(isbn):
        raise ValueError(f'{path.name}: {isbn} is not a valid ISBN-13')
    with zipfile.ZipFile(path) as archive:
        spreads = [name for name in archive.namelist() if name.startswith('Spreads/Spread_')]
        if len(spreads) != 1:
            raise ValueError(f'{path.name}: expected one spread, found {len(spreads)}')
        spread = ET.fromstring(archive.read(spreads[0])).find('Spread')
    page = spread.find('Page')
    top, left, bottom, right = (float(v) for v in page.get('GeometricBounds').split())
    page_matrix = _matrix(page.get('ItemTransform'))
    # A point of the spread at (x, y) is at (x - page_x, y - page_y) from the page's top left corner.
    origin_x, origin_y = page_matrix[4] + left, page_matrix[5] + top

    guides: dict[str, float] = {}
    for guide in page.findall('Guide'):
        label = guide.find('.//KeyValuePair').get('Value')
        guides.setdefault(label.lower(), float(guide.get('Location')))

    shapes: dict[str, Box] = {}
    identity = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    for item in spread:
        if item.tag in ('Page', 'FlattenerPreference'):
            continue
        name = item.get('Name')
        if not name:
            continue
        box = _shape_box(item, identity)
        if box:
            shapes[name] = Box(box.x0 - origin_x, box.y0 - origin_y, box.x1 - origin_x, box.y1 - origin_y)

    def need(label: str) -> float:
        try:
            return guides[label.lower()]
        except KeyError:
            raise ValueError(f'{path.name}: guide {label} not found') from None

    def shape(label: str) -> Box:
        try:
            return shapes[label]
        except KeyError:
            raise ValueError(f'{path.name}: shape {label} not found') from None

    top_trim, bottom_trim = need('GuideTopTrim'), need('GuideBottomTrim')
    top_safe = need('GuideTopsafety')
    bottom_safe = need('GuideBottomsafety')
    back_cov, spine_shape, front_cov = shape('BackCov'), shape('Spine'), shape('FrontCov')
    art = Box(back_cov.x0, min(back_cov.y0, spine_shape.y0, front_cov.y0),
              front_cov.x1, max(back_cov.y1, spine_shape.y1, front_cov.y1))
    if kind == 'perfect':
        back = Box(need('GuideBackLeftTrim'), top_trim, need('GuideSpineLeft'), bottom_trim)
        front = Box(need('GuideSpineRight'), top_trim, need('GuideFrontRightTrim'), bottom_trim)
    else:  # the board's faces; the hinges (0.5 in) sit between each board and the spine
        back = Box(need('GuideBackLeftTrim'), top_trim, need('GuideBackRightBoard'), bottom_trim)
        front = Box(need('GuideFrontLeftBoard'), top_trim, need('GuideFrontRightTrim'), bottom_trim)
    spine = Box(need('GuideSpineLeft'), top_trim, need('GuideSpineRight'), bottom_trim)
    return Template(
        path=path, isbn=isbn, kind=kind,
        page=Box(0.0, 0.0, right - left, bottom - top),
        art=art, back=back, spine=spine, front=front,
        back_safe=Box(need('GuideBackLeftSafety'), top_safe, need('GuideBackRightSafety'), bottom_safe),
        spine_safe=Box(need('GuideSpineLeftSafety'), top_safe, need('GuideSpineRightSafety'), bottom_safe),
        front_safe=Box(need('GuideFrontLeftSafety'), top_safe, need('GuideFrontRightSafety'), bottom_safe),
        barcode=shape('BarcodeGroup'), guides=guides, shapes=shapes,
    )


def find_templates(folder: Path) -> list[Path]:
    return sorted(p for p in Path(folder).glob('*.idml') if ISBN_IN_NAME.match(p.name))
