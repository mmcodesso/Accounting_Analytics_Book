"""The PowerPoint template every deck uses, built in code from Pandoc's default reference document.

Pandoc picks a slide layout by name (Title Slide, Section Header, Title and Content, Two Content,
Comparison, Content with Caption, Blank) and takes its geometry, fonts, colors, backgrounds and
footer from the reference document. This module themes those layouts with the tokens of
slides/theme/tokens.yml so the PowerPoint decks match the Reveal.js ones:

- the title slide on the book's blue, the book title as a kicker above the chapter title;
- module dividers (Section Header) on blue with white type;
- content slides with the title over a thin rule, top-aligned text, and the footer
  "Chapter N · <title>" with the slide number (Pandoc copies them from the layouts);
- tables and figure captions at the smaller table size (the cells' colors are written by
  pptx_finish.py, because PowerPoint draws only its built-in table styles);
- empty document properties, so no name travels with the file.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'a': A, 'p': P}
for prefix, uri in (('a', A), ('p', P), ('r', R)):
    ET.register_namespace(prefix, uri)
EMU = 914400
WIDTH, HEIGHT = 13.333333, 7.5
MARGIN = 0.6
TOP, BOTTOM = 1.6, 6.8
GAP = 0.4
LAYOUTS = {'Title Slide', 'Title and Content', 'Section Header', 'Two Content',
           'Comparison', 'Content with Caption', 'Blank'}
RULED = {'Title and Content', 'Two Content', 'Comparison', 'Content with Caption', 'Title Only',
         'Picture with Caption'}
SCHEME = {'dk1': 'ink', 'lt1': 'paper', 'dk2': 'blue', 'lt2': 'tint', 'accent1': 'blue',
          'accent2': 'teal', 'accent3': 'gray', 'accent4': 'coral', 'accent5': 'amber',
          'accent6': 'blue', 'hlink': 'blue', 'folHlink': 'teal'}


def q(prefix: str, tag: str) -> str:
    return f'{{{NS[prefix]}}}{tag}'


def emu(value: float) -> str:
    return str(round(value * EMU))


def placeholder_box(layout: str, kind: str, idx: int) -> tuple[float, float, float, float]:
    half = (WIDTH - 2 * MARGIN - GAP) / 2
    if kind == 'ftr':
        return (MARGIN, 7.0, 9.6, 0.3)
    if kind == 'sldNum':
        return (WIDTH - MARGIN - 1.2, 7.0, 1.2, 0.3)
    if kind == 'dt':
        return (MARGIN + 9.8, 7.0, 1.5, 0.3)
    if layout == 'Title Slide':
        return (0.9, 2.95, 11.5, 2.6) if kind == 'ctrTitle' else (0.9, 1.75, 11.5, 0.7)
    if layout == 'Section Header':
        return (0.9, 2.3, 11.5, 2.9) if kind == 'title' else (0.9, 5.3, 11.5, 0.8)
    if kind == 'title':
        return (MARGIN, 0.3, WIDTH - 2 * MARGIN, 1.0)
    if layout == 'Two Content':
        return (MARGIN if idx == 1 else MARGIN + half + GAP, TOP, half, BOTTOM - TOP)
    if layout == 'Comparison':
        x = MARGIN + half + GAP if idx in (3, 4) else MARGIN
        return (x, TOP, half, 0.6) if idx in (1, 3) else (x, TOP + 0.7, half, BOTTOM - TOP - 0.7)
    if layout in {'Content with Caption', 'Picture with Caption'}:
        # Text before a figure or table goes above it, at full width.
        if kind == 'body':
            return (MARGIN, TOP - 0.05, WIDTH - 2 * MARGIN, 0.5)
        return (MARGIN, TOP + 0.55, WIDTH - 2 * MARGIN, BOTTOM - TOP - 0.55)
    return (MARGIN, TOP, WIDTH - 2 * MARGIN, BOTTOM - TOP)


def placeholder_style(layout: str, kind: str, tokens: dict) -> dict:
    """Size (pt), color, weight, alignment and anchor of one placeholder's first level."""
    colors, sizes = tokens['colors'], tokens['sizes']
    dark = layout in {'Title Slide', 'Section Header'}
    if kind in {'ftr', 'sldNum', 'dt'}:
        return {'size': sizes['attribution'], 'color': colors['tint' if dark else 'gray'],
                'align': 'r' if kind == 'sldNum' else 'l', 'anchor': 'ctr'}
    if layout == 'Title Slide':
        if kind == 'ctrTitle':
            return {'size': sizes['opening'], 'color': colors['paper'], 'bold': True, 'anchor': 't'}
        return {'size': sizes['evidence'], 'color': colors['tint'], 'bold': True, 'anchor': 'b'}
    if layout == 'Section Header':
        if kind == 'title':
            return {'size': sizes['opening'], 'color': colors['paper'], 'bold': True, 'anchor': 'ctr'}
        return {'size': sizes['evidence'], 'color': colors['tint'], 'anchor': 't'}
    if kind == 'title':
        return {'size': sizes['title'], 'color': colors['blue'], 'bold': True, 'anchor': 'b'}
    if kind == 'body' and layout in {'Content with Caption', 'Picture with Caption'}:
        return {'size': sizes['evidence'], 'color': colors['gray'], 'anchor': 't'}
    return {'size': sizes['body'], 'color': colors['ink'], 'anchor': 't'}


def set_xfrm(sp: ET.Element, box: tuple[float, float, float, float]) -> None:
    properties = sp.find('p:spPr', NS)
    if properties is None:
        properties = ET.SubElement(sp, q('p', 'spPr'))
    for old in properties.findall('a:xfrm', NS):
        properties.remove(old)
    transform = ET.Element(q('a', 'xfrm'))
    properties.insert(0, transform)
    x, y, w, h = box
    ET.SubElement(transform, q('a', 'off'), x=emu(x), y=emu(y))
    ET.SubElement(transform, q('a', 'ext'), cx=emu(w), cy=emu(h))


def solid(parent: ET.Element, color: str) -> ET.Element:
    fill = ET.SubElement(parent, q('a', 'solidFill'))
    ET.SubElement(fill, q('a', 'srgbClr'), val=color)
    return fill


def set_run_style(prop: ET.Element, style: dict) -> None:
    prop.set('sz', str(round(style['size'] * 100)))
    prop.attrib.pop('cap', None)
    if style.get('bold'):
        prop.set('b', '1')
    for old in prop.findall('a:solidFill', NS):
        prop.remove(old)
    fill = ET.Element(q('a', 'solidFill'))
    ET.SubElement(fill, q('a', 'srgbClr'), val=style['color'])
    prop.insert(0, fill)


def style_placeholder(sp: ET.Element, style: dict, footer: str | None) -> None:
    body = sp.find('p:txBody', NS)
    if body is None:
        return
    props = body.find('a:bodyPr', NS)
    if props is None:
        props = ET.Element(q('a', 'bodyPr'))
        body.insert(0, props)
    props.set('anchor', style['anchor'])
    props.set('wrap', 'square')
    for old in list(props):
        props.remove(old)
    ET.SubElement(props, q('a', 'normAutofit'))
    lst = body.find('a:lstStyle', NS)
    if lst is None:
        lst = ET.Element(q('a', 'lstStyle'))
        body.insert(1, lst)
    level = lst.find('a:lvl1pPr', NS)
    if level is None:
        level = ET.Element(q('a', 'lvl1pPr'))
        lst.insert(0, level)
    level.set('algn', style.get('align', 'l'))
    if style['anchor'] != 't' or style.get('bold'):
        level.set('marL', '0')
        level.set('indent', '0')
    prop = level.find('a:defRPr', NS)
    if prop is None:
        prop = ET.SubElement(level, q('a', 'defRPr'))
    set_run_style(prop, style)
    for paragraph in body.findall('a:p', NS):
        properties = paragraph.find('a:pPr', NS)
        if properties is not None:
            properties.set('algn', style.get('align', 'l'))
        for run in paragraph.findall('.//a:rPr', NS):
            run.attrib.pop('sz', None)
    if footer is not None:
        for paragraph in body.findall('a:p', NS):
            body.remove(paragraph)
        paragraph = ET.SubElement(body, q('a', 'p'))
        run = ET.SubElement(paragraph, q('a', 'r'))
        ET.SubElement(run, q('a', 'rPr'), lang='en-US')
        ET.SubElement(run, q('a', 't')).text = footer


def add_line(tree: ET.Element, shape_id: int, name: str, box: tuple[float, float, float], color: str,
             width_pt: float) -> None:
    x, y, length = box
    shape = ET.SubElement(tree, q('p', 'cxnSp'))
    nv = ET.SubElement(shape, q('p', 'nvCxnSpPr'))
    ET.SubElement(nv, q('p', 'cNvPr'), id=str(shape_id), name=name)
    ET.SubElement(nv, q('p', 'cNvCxnSpPr'))
    ET.SubElement(nv, q('p', 'nvPr'), userDrawn='1')
    properties = ET.SubElement(shape, q('p', 'spPr'))
    transform = ET.SubElement(properties, q('a', 'xfrm'))
    ET.SubElement(transform, q('a', 'off'), x=emu(x), y=emu(y))
    ET.SubElement(transform, q('a', 'ext'), cx=emu(length), cy='0')
    geometry = ET.SubElement(properties, q('a', 'prstGeom'), prst='line')
    ET.SubElement(geometry, q('a', 'avLst'))
    line = ET.SubElement(properties, q('a', 'ln'), w=str(round(width_pt * 12700)))
    solid(line, color)


def set_background(common: ET.Element, color: str) -> None:
    for old in common.findall('p:bg', NS):
        common.remove(old)
    background = ET.Element(q('p', 'bg'))
    properties = ET.SubElement(background, q('p', 'bgPr'))
    solid(properties, color)
    ET.SubElement(properties, q('a', 'effectLst'))
    common.insert(0, background)


def theme_layout(xml: ET.Element, tokens: dict, footer: str) -> str:
    colors = tokens['colors']
    common = xml.find('p:cSld', NS)
    layout = common.get('name', '')
    if layout in {'Title Slide', 'Section Header'}:
        set_background(common, colors['blue'])
    tree = common.find('p:spTree', NS)
    for sp in tree.findall('p:sp', NS):
        ph = sp.find('p:nvSpPr/p:nvPr/p:ph', NS)
        if ph is None:
            continue
        kind, idx = ph.get('type', 'obj'), int(ph.get('idx', '0'))
        set_xfrm(sp, placeholder_box(layout, kind, idx))
        style_placeholder(sp, placeholder_style(layout, kind, tokens), footer if kind == 'ftr' else None)
    if layout in RULED:
        add_line(tree, 901, 'Title Rule', (MARGIN, 1.42, WIDTH - 2 * MARGIN), colors['rule'], 1.5)
    if layout == 'Title Slide':
        add_line(tree, 901, 'Accent Rule', (0.9, 2.65, 2.6), colors['highlight'], 4)
    return layout


def theme_master(xml: ET.Element, tokens: dict) -> None:
    colors, sizes = tokens['colors'], tokens['sizes']
    tree = xml.find('p:cSld/p:spTree', NS)
    for sp in tree.findall('p:sp', NS):
        ph = sp.find('p:nvSpPr/p:nvPr/p:ph', NS)
        if ph is not None:
            set_xfrm(sp, placeholder_box('Master', ph.get('type', 'obj'), int(ph.get('idx', '0'))))
    # Footer and slide number on every layout but the title slide; never the date.
    for old in xml.findall('p:hf', NS):
        xml.remove(old)
    styles = xml.find('p:txStyles', NS)
    xml.insert(list(xml).index(styles), ET.Element(q('p', 'hf'), hdr='0', dt='0'))
    levels = {'titleStyle': [('title', True)],
              'bodyStyle': [('body', False), ('evidence', False), ('evidence', False)],
              'otherStyle': [('table', False)]}
    for name, roles in levels.items():
        style = styles.find(f'p:{name}', NS)
        for number, (role, bold) in enumerate(roles, start=1):
            level = style.find(f'a:lvl{number}pPr', NS)
            if level is None:
                continue
            level.set('algn', 'l')
            if name == 'bodyStyle':
                for tag in ('spcBef', 'spcAft'):
                    for old in level.findall(f'a:{tag}', NS):
                        level.remove(old)
                after = ET.Element(q('a', 'spcAft'))
                ET.SubElement(after, q('a', 'spcPts'), val='900')
                before = ET.Element(q('a', 'spcBef'))
                ET.SubElement(before, q('a', 'spcPts'), val='0')
                level.insert(0, after)
                level.insert(0, before)
            prop = level.find('a:defRPr', NS)
            set_run_style(prop, {'size': sizes[role], 'bold': bold,
                                 'color': colors['blue' if name == 'titleStyle' else 'ink']})


def theme_reference(source: Path, target: Path, tokens: dict, *, footer: str = '') -> None:
    """Write the themed reference document for one deck (the footer names its chapter)."""
    colors, sizes = tokens['colors'], tokens['sizes']
    found = set()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as out:
        for name in src.namelist():
            data = src.read(name)
            if name == 'docProps/core.xml':
                text = data.decode('utf-8')
                for tag in ('dc:title', 'dc:creator', 'cp:lastModifiedBy'):
                    text = re.sub(rf'<{tag}>[^<]*</{tag}>', f'<{tag}></{tag}>', text)
                data = text.encode('utf-8')
            elif name.startswith('ppt/') and name.endswith('.xml'):
                xml = ET.fromstring(data)
                for font in xml.iter(q('a', 'latin')):
                    if not font.get('typeface', '').startswith('+'):
                        font.set('typeface', tokens['font'])
                if name == 'ppt/presentation.xml':
                    size = xml.find('p:sldSz', NS)
                    size.set('cx', emu(WIDTH))
                    size.set('cy', emu(HEIGHT))
                    size.set('type', 'screen16x9')
                    xml.set('showSpecialPlsOnTitleSld', '0')
                    # Tables and figure captions take the document's default text size.
                    for prop in xml.findall('p:defaultTextStyle//a:defRPr', NS):
                        prop.set('sz', str(sizes['table'] * 100))
                elif name.startswith('ppt/theme/'):
                    scheme = xml.find('.//a:clrScheme', NS)
                    if scheme is not None:
                        for slot in scheme:
                            role = SCHEME.get(slot.tag.split('}')[-1])
                            if role:
                                for child in list(slot):
                                    slot.remove(child)
                                ET.SubElement(slot, q('a', 'srgbClr'), val=colors[role])
                    for font in xml.findall('.//a:fontScheme//a:latin', NS):
                        font.set('typeface', tokens['font'])
                elif name.startswith('ppt/slideMasters/'):
                    theme_master(xml, tokens)
                elif name.startswith('ppt/slideLayouts/'):
                    found.add(theme_layout(xml, tokens, footer))
                data = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
            out.writestr(name, data)
    missing = LAYOUTS - found
    if missing:
        raise ValueError(f'Reference template lacks layouts: {sorted(missing)}')
