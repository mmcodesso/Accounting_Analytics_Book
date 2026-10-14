"""The layout of a print cover as a Draw.io file.

The cover is drawn in Draw.io like the book's other figures (and like visuals/cover/accounting_analytics_cover.drawio,
the front cover this one grows from): one page the size of the template's bleed box, a background picture,
text, rules, and IngramSpark's barcode. Units are Draw.io pixels, 96 to the inch, from the bleed box's top
left corner. The positions come from the template's zones (scripts/print/cover_template.py): the front
cover's text sits where it sits on the 8.5 x 11 in front cover, whatever the trim, and the back cover and
the spine are laid out inside the safe areas. `scripts/print/cover.py` turns the file into the PDF.

The background in the Draw.io file is a small copy of the artwork, enough to place the text. The print PDF
paints the full-resolution CMYK artwork (scripts/print/cover_art.py) under the Draw.io text instead.
"""
from __future__ import annotations

import base64
import html
from dataclasses import dataclass

from scripts.print.cover_barcode import Barcode, stencil_style
from scripts.print.cover_template import PT, Template

PX = 96 / PT                     # Draw.io pixels per point of the page
WHITE, GOLD, BLACK = '#FFFFFF', '#E3A93B', '#000000'
FRONT_ORIGINAL = (612.0, 792.0)  # the 8.5 x 11 in page the front cover's positions were drawn on, in points
MARGIN = 66                      # the front cover's left margin, in pixels of that page


@dataclass
class Cell:
    id: str
    style: str
    x: float
    y: float
    w: float
    h: float
    value: str = ''

    def xml(self) -> str:
        return (f'<mxCell id="{self.id}" parent="1" style="{self.style}" value="{html.escape(self.value, quote=True)}" '
                f'vertex="1"><mxGeometry x="{self.x:.2f}" y="{self.y:.2f}" width="{self.w:.2f}" '
                f'height="{self.h:.2f}" as="geometry"/></mxCell>')


def text_style(color: str = WHITE, size: int = 16, bold: bool = False, align: str = 'left',
               valign: str = 'top', rotation: int = 0, extra: str = '') -> str:
    return ('text;html=1;whiteSpace=wrap;overflow=visible;strokeColor=none;fillColor=none;'
            f'fontColor={color};fontSize={size};fontStyle={1 if bold else 0};fontFamily=Helvetica;'
            f'align={align};verticalAlign={valign};spacing=0;spacingLeft=0;spacingRight=0;spacingTop=0;'
            f'spacingBottom=0;{f"rotation={rotation};" if rotation else ""}{extra}')


def spaced(text: str, pixels: float) -> str:
    return f'<span style="letter-spacing:{pixels}px">{html.escape(text)}</span>'


class Cover:
    """One cover's cells, positioned from the template's zones."""

    def __init__(self, template: Template, copy: dict, edition: str, barcode: Barcode,
                 background_jpeg: bytes):
        self.t = template
        self.copy = copy
        self.edition = edition
        self.barcode = barcode
        self.background = background_jpeg
        self.cells: list[Cell] = []
        self.width = template.art.w * PX
        self.height = template.art.h * PX

    # -- coordinates ---------------------------------------------------------------------------
    def x(self, point: float) -> float:
        return (point - self.t.art.x0) * PX

    def y(self, point: float) -> float:
        return (point - self.t.art.y0) * PX

    def add(self, cell: Cell) -> Cell:
        self.cells.append(cell)
        return cell

    # -- background and barcode ----------------------------------------------------------------
    def background_cell(self) -> None:
        data = base64.b64encode(self.background).decode()
        self.add(Cell('background-image',
                      f'shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;aspect=fixed;'
                      f'image=data:image/jpeg,{data};locked=1;', 0, 0, self.width, self.height))

    def barcode_cells(self) -> None:
        box = self.barcode.box
        x, y, w, h = self.x(box.x0), self.y(box.y0), box.w * PX, box.h * PX
        self.add(Cell('barcode-box', f'rounded=0;fillColor={WHITE};strokeColor=none;', x, y, w, h))
        self.add(Cell('barcode', f'{stencil_style(self.barcode)};fillColor={BLACK};strokeColor=none;aspect=fixed;',
                      x, y, w, h))

    # -- front -----------------------------------------------------------------------------------
    def front(self) -> None:
        f = self.copy['front']
        # The front picture's top left corner: the 8.5 x 11 in page sits at the face's bottom right.
        left = self.x(self.t.front.x1 - FRONT_ORIGINAL[0])
        top = self.y(self.t.front.y1 - FRONT_ORIGINAL[1])

        def at(ox: float, oy: float) -> tuple[float, float]:
            return left + ox, top + oy

        x, y = at(MARGIN, 44)
        self.add(Cell('edition', text_style(WHITE, 17, True, valign='middle'), x, y, 520, 30,
                      spaced(self.edition.upper(), 5)))
        for index, line in enumerate(f['title']):
            x, y = at(MARGIN, 84 + 78 * index)
            self.add(Cell(f'title-{index + 1}', text_style(WHITE, 52, True, valign='middle'), x, y, 640, 76,
                          html.escape(line)))
        x, y = at(MARGIN, 282)
        self.add(Cell('subtitle', text_style(GOLD, 27, True, valign='middle'), x, y, 600, 46,
                      html.escape(f['subtitle'])))
        x, y = at(MARGIN, 358)
        self.add(Cell('subtitle-rule', f'shape=line;strokeColor={GOLD};strokeWidth=3;', x, y, 76, 1))
        x, y = at(MARGIN, 390)
        self.add(Cell('author', text_style(WHITE, 22, True, valign='middle'), x, y, 520, 44,
                      html.escape(f['author'])))
        x, y = at(MARGIN, 914)
        self.add(Cell('publisher-rule', f'shape=line;strokeColor={GOLD};strokeWidth=3;', x, y, 76, 1))
        x, y = at(MARGIN, 944)
        self.add(Cell('publisher', text_style(WHITE, 19, True, valign='middle'), x, y, 460, 36,
                      html.escape(f['publisher'])))

    # -- spine -----------------------------------------------------------------------------------
    def spine(self) -> None:
        s = self.copy['spine']
        center_x = self.x((self.t.spine.x0 + self.t.spine.x1) / 2)
        top, bottom = self.y(self.t.spine.y0), self.y(self.t.spine.y1)
        edge = 0.55 * 96                       # from the head and the foot of the book to the text
        thickness = 84
        top_length = 6.6 * 96
        bottom_length = 3.1 * 96
        # Rotated 90 degrees clockwise, so the text reads downward; the first line is the right one.
        self.add(Cell('spine-title', text_style(WHITE, 40, True, valign='middle', rotation=90),
                      center_x - top_length / 2, top + edge + top_length / 2 - thickness / 2, top_length, thickness,
                      f'<div style="line-height:46px">{html.escape(s["title"])}</div>'
                      f'<div style="font-size:17px;line-height:22px;margin-top:8px;color:{GOLD}">'
                      f'{html.escape(s["subtitle"])}</div>'))
        self.add(Cell('spine-author', text_style(WHITE, 22, True, align='right', valign='middle', rotation=90),
                      center_x - bottom_length / 2, bottom - edge - bottom_length / 2 - thickness / 2,
                      bottom_length, thickness,
                      f'<div style="line-height:28px">{html.escape(s["author"])}</div>'
                      f'<div style="font-size:14px;line-height:20px;margin-top:8px">{html.escape(s["publisher"])}</div>'))

    # -- back ------------------------------------------------------------------------------------
    def back(self) -> None:
        b = self.copy['back']
        face = self.t.back
        left = self.x(face.x0) + MARGIN
        top = self.y(face.y0)
        width = min(640, (face.w * PX) - 2 * MARGIN)
        paragraphs = ''.join(f'<p style="margin:0 0 14px 0">{p.strip()}</p>' for p in b['paragraphs'])
        features = ''.join(
            f'<li style="color:{GOLD};margin-bottom:6px"><span style="color:{WHITE}">{html.escape(f)}</span></li>'
            for f in b['features'])
        body = (f'<div style="font-size:30px;line-height:36px;font-weight:bold;margin-bottom:14px">'
                f'{"<br>".join(html.escape(line) for line in b["headline"])}</div>'
                f'<div style="width:76px;border-top:3px solid {GOLD};margin-bottom:22px"></div>'
                f'<div style="line-height:23px">{paragraphs}'
                f'<ul style="margin:6px 0 14px 0;padding-left:22px;line-height:22px">{features}</ul>'
                f'<p style="margin:0">{html.escape(b["audience"])}</p></div>')
        self.add(Cell('back-copy', text_style(WHITE, 16, False), left, top + 84, width, 720, body))
        if b.get('bio'):
            self.add(Cell('back-bio', text_style(WHITE, 13, False), left, top + 800, width, 70,
                          f'<div style="line-height:19px">{b["bio"].strip()}</div>'))
        # The footer: bottom left, level with the foot of the barcode, clear of its box.
        foot = self.y(self.barcode.box.y1)
        footer = b['footer']
        lines = (f'<div style="line-height:19px">{html.escape(footer[0])}</div>'
                 f'<div style="line-height:19px">{html.escape(footer[1])}</div>'
                 f'<div style="line-height:22px;font-weight:bold;color:{GOLD};font-size:15px">{html.escape(footer[2])}</div>')
        self.add(Cell('back-footer', text_style(WHITE, 13, False, valign='bottom'), left, foot - 70, 520, 70, lines))

    def build(self) -> str:
        self.cells = []
        self.background_cell()
        self.front()
        self.spine()
        self.back()
        self.barcode_cells()
        body = '\n        '.join(cell.xml() for cell in self.cells)
        return (
            '<mxfile host="Electron" version="29.6.6">\n'
            f'  <diagram id="cover-wrap" name="{html.escape(self.t.kind)} cover {self.t.isbn}">\n'
            '    <mxGraphModel dx="1584" dy="936" grid="1" gridSize="10" guides="1" tooltips="1" connect="0" '
            f'arrows="0" fold="1" page="1" pageScale="1" pageWidth="{self.width:.2f}" pageHeight="{self.height:.2f}" '
            'math="0" shadow="0">\n'
            '      <root>\n        <mxCell id="0" />\n        <mxCell id="1" parent="0" />\n        '
            f'{body}\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')
