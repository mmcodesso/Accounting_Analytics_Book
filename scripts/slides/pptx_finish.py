"""Finish a rendered PowerPoint deck: give its tables and figure captions the Reveal.js look.

PowerPoint draws only its built-in table styles (a custom style stored in the file is kept but not
drawn), and Pandoc gives every table the built-in "Medium Style 2 - Accent 1". So this step writes the
book's table look into each cell instead: a blue header row with white bold text, light banded rows
and thin horizontal rules. The tables stay native and editable. Figure captions, which Pandoc writes
at the body size, get the smaller gray type of the Reveal captions.
"""
from __future__ import annotations

import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .pptx_theme import NS, q

SLIDE = re.compile(r'ppt/slides/slide\d+\.xml')
RULE_WIDTH = '9525'  # 0.75 pt


def _line(tag: str, color: str | None) -> ET.Element:
    line = ET.Element(q('a', tag), w=RULE_WIDTH if color else '0')
    if color:
        fill = ET.SubElement(line, q('a', 'solidFill'))
        ET.SubElement(fill, q('a', 'srgbClr'), val=color)
    else:
        ET.SubElement(line, q('a', 'noFill'))
    return line


def format_table(table: ET.Element, colors: dict) -> None:
    properties = table.find('a:tblPr', NS)
    if properties is not None:
        for style in properties.findall('a:tableStyleId', NS):
            properties.remove(style)
    for number, row in enumerate(table.findall('a:tr', NS)):
        header = number == 0
        fill_color = colors['blue'] if header else (colors['tint'] if number % 2 else colors['paper'])
        for cell in row.findall('a:tc', NS):
            old = cell.find('a:tcPr', NS)
            margins = dict(old.attrib) if old is not None else {}
            if old is not None:
                cell.remove(old)
            cell_properties = ET.SubElement(cell, q('a', 'tcPr'), margins)
            for tag in ('lnL', 'lnR', 'lnT'):
                cell_properties.append(_line(tag, None))
            cell_properties.append(_line('lnB', None if header else colors['rule']))
            fill = ET.SubElement(cell_properties, q('a', 'solidFill'))
            ET.SubElement(fill, q('a', 'srgbClr'), val=fill_color)
            for run in cell.iter(q('a', 'rPr')):
                for old_fill in run.findall('a:solidFill', NS):
                    run.remove(old_fill)
                text_fill = ET.Element(q('a', 'solidFill'))
                ET.SubElement(text_fill, q('a', 'srgbClr'), val=colors['paper'] if header else colors['ink'])
                run.insert(0, text_fill)
                if header:
                    run.set('b', '1')


def format_captions(slide: ET.Element, tokens: dict) -> None:
    """Pandoc writes a figure's caption as a text box in the body placeholder, at the body size."""
    if slide.find('.//p:pic', NS) is None:
        return
    for shape in slide.iter(q('p', 'sp')):
        marker = shape.find('p:nvSpPr/p:cNvSpPr', NS)
        if marker is None or marker.get('txBox') != '1':
            continue
        for run in shape.iter(q('a', 'rPr')):
            run.set('sz', str(tokens['sizes']['evidence'] * 100))
            for old in run.findall('a:solidFill', NS):
                run.remove(old)
            fill = ET.Element(q('a', 'solidFill'))
            ET.SubElement(fill, q('a', 'srgbClr'), val=tokens['colors']['gray'])
            run.insert(0, fill)


def finish(path: Path, tokens: dict) -> None:
    """Rewrite the deck in place; only slides with a table or a figure change."""
    colors = tokens['colors']
    temporary = path.with_name(f'.{path.name}.tmp')
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if SLIDE.fullmatch(item.filename) and (b'<a:tbl>' in data or b'<p:pic>' in data):
                xml = ET.fromstring(data)
                for table in xml.iter(q('a', 'tbl')):
                    format_table(table, colors)
                format_captions(xml, tokens)
                data = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
            target.writestr(item, data)
    shutil.move(temporary, path)
