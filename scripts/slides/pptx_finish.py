"""Finish a rendered PowerPoint deck: give its tables and figure captions the Reveal.js look.

PowerPoint draws only its built-in table styles (a custom style stored in the file is kept but not
drawn), and Pandoc gives every table the built-in "Medium Style 2 - Accent 1". So this step writes the
book's table look into each cell instead: a blue header row with white bold text, light banded rows
and thin horizontal rules. The tables stay native and editable. Figure captions, which Pandoc writes
at the body size, get the smaller gray type of the Reveal captions; a caption too long for one line
gets the room for its lines from the picture above it. Numbered lists get numbers in the body font
and room for two digits.
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
EMU_PER_POINT = 12700
CHARACTER_WIDTH = 0.47  # the average width of Arial text, as a share of its size
BOX_INSET = 7.2         # PowerPoint's default left and right text insets, in points
NUMBER_GAP = 6          # the least space between a list number and its text, in points
ROADMAP_TITLE = 'In this chapter'
ROADMAP_CHARACTERS = 30  # characters that fit a line of a roadmap column (slides/filters/deck.lua)
ROADMAP_LINES = 12       # lines a roadmap column holds at the body size (slides/filters/deck.lua)


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


def caption_lines(text: str, width: int, size: float) -> int:
    """About how many lines a caption of this many characters takes in a box this wide (EMU) at this size."""
    per_line = max(1, int((width / EMU_PER_POINT - 2 * BOX_INSET) / (CHARACTER_WIDTH * size)))
    return max(1, -(-len(text) // per_line))


def make_room(picture: ET.Element, caption: ET.Element, lines: int, size: float) -> None:
    """Pandoc sizes a caption box for one line, right under the picture. For more lines, the box grows
    upward and the picture shrinks by the same height, keeping its proportions and its center."""
    extra = round((lines - 1) * size * 1.2 * EMU_PER_POINT)
    box = caption.find('p:spPr/a:xfrm', NS)
    frame = picture.find('p:spPr/a:xfrm', NS)
    if extra <= 0 or box is None or frame is None:
        return
    box_off, box_ext = box.find('a:off', NS), box.find('a:ext', NS)
    box_off.set('y', str(int(box_off.get('y')) - extra))
    box_ext.set('cy', str(int(box_ext.get('cy')) + extra))
    off, ext = frame.find('a:off', NS), frame.find('a:ext', NS)
    width, height = int(ext.get('cx')), int(ext.get('cy'))
    new_height = height - extra
    if new_height <= 0:
        return
    new_width = round(width * new_height / height)
    off.set('x', str(int(off.get('x')) + (width - new_width) // 2))
    ext.set('cx', str(new_width))
    ext.set('cy', str(new_height))


def format_captions(slide: ET.Element, tokens: dict) -> None:
    """Pandoc writes a figure's caption as a text box in the body placeholder, at the body size."""
    pictures = list(slide.iter(q('p', 'pic')))
    if not pictures:
        return
    size = tokens['sizes']['evidence']
    for shape in slide.iter(q('p', 'sp')):
        marker = shape.find('p:nvSpPr/p:cNvSpPr', NS)
        if marker is None or marker.get('txBox') != '1':
            continue
        for run in shape.iter(q('a', 'rPr')):
            run.set('sz', str(size * 100))
            for old in run.findall('a:solidFill', NS):
                run.remove(old)
            fill = ET.Element(q('a', 'solidFill'))
            ET.SubElement(fill, q('a', 'srgbClr'), val=tokens['colors']['gray'])
            run.insert(0, fill)
        ext = shape.find('p:spPr/a:xfrm/a:ext', NS)
        if len(pictures) == 1 and ext is not None:
            text = ''.join(node.text or '' for node in shape.iter(q('a', 't')))
            make_room(pictures[0], shape, caption_lines(text, int(ext.get('cx')), size), size)


def format_lists(slide: ET.Element, tokens: dict) -> None:
    """Pandoc's hanging indent leaves a list number no room for two digits, and PowerPoint draws the
    number of an item that opens with code in the wider code font (it ignores the bullet font for
    that), so the number runs into the text. A list gets the indent its widest number needs, and its
    numbers the body font where PowerPoint honors it."""
    size = tokens['sizes']['body']
    for body in slide.iter(q('p', 'txBody')):
        numbered = [pr for pr in body.findall('a:p/a:pPr', NS) if pr.find('a:buAutoNum', NS) is not None]
        if not numbered:
            continue
        highest = max(int(pr.find('a:buAutoNum', NS).get('startAt', '1')) for pr in numbered) + len(numbered) - 1
        code_first = any(
            (paragraph.find('a:r/a:rPr/a:latin', NS) is not None
             and paragraph.find('a:r/a:rPr/a:latin', NS).get('typeface') == tokens.get('code_font'))
            for paragraph in body.findall('a:p', NS) if paragraph.find('a:pPr/a:buAutoNum', NS) is not None)
        # Arial digits are 0.556 em and the period 0.278 em; every character of a code font is 0.55 em.
        width = (len(str(highest)) + 1) * 0.55 if code_first else len(str(highest)) * 0.556 + 0.278
        needed = round((width * size + NUMBER_GAP) * EMU_PER_POINT)
        for pr in numbered:
            if pr.find('a:buFont', NS) is None:
                auto = pr.find('a:buAutoNum', NS)
                pr.insert(list(pr).index(auto), ET.Element(q('a', 'buFont'), typeface=tokens['font']))
            if needed > int(pr.get('marL', '0')):
                pr.set('marL', str(needed))
                pr.set('indent', str(-needed))


def format_code(slide: ET.Element, tokens: dict) -> None:
    """A code block reaches PowerPoint as a paragraph whose runs are all in the code font, at the body
    size; it gets the evidence size, as Reveal's code blocks do, so a query's lines do not wrap."""
    size = str(tokens['sizes']['evidence'] * 100)
    for paragraph in slide.iter(q('a', 'p')):
        runs = paragraph.findall('a:r', NS)
        if not runs or paragraph.find('a:pPr/a:buNone', NS) is None:
            continue
        fonts = [run.find('a:rPr/a:latin', NS) for run in runs]
        if all(font is not None and font.get('typeface') == tokens.get('code_font') for font in fonts):
            for run in runs:
                run.find('a:rPr', NS).set('sz', size)


def roadmap_lines(text: str) -> int:
    """Lines a roadmap entry takes in a column, as slides/filters/deck.lua estimates them."""
    return max(1, -(-len(text) // ROADMAP_CHARACTERS))


def format_roadmap(slide: ET.Element, tokens: dict) -> None:
    """A long chapter's two-column roadmap gets the evidence size, as Reveal's roadmap-compact class does:
    the layout's half placeholders hold about ROADMAP_LINES lines at the body size."""
    shapes = list(slide.iter(q('p', 'sp')))
    title = next((shape for shape in shapes if shape.find('.//p:ph[@type="title"]', NS) is not None), None)
    if title is None or ''.join(t.text or '' for t in title.iter(q('a', 't'))).strip() != ROADMAP_TITLE:
        return
    columns = [shape for shape in shapes if shape.find('.//p:ph[@sz="half"]', NS) is not None]
    def markdown(paragraph: ET.Element) -> str:
        # deck.lua counts the Markdown it writes: "- " before each module and "**" around the Part's name.
        text = ''.join(t.text or '' for t in paragraph.iter(q('a', 't')))
        if paragraph.find('a:pPr/a:buNone', NS) is None:
            return '- ' + text
        run = paragraph.find('a:r/a:rPr', NS)
        return f'**{text}**' if run is not None and run.get('b') == '1' else text
    def column_lines(shape: ET.Element) -> int:
        return sum(roadmap_lines(markdown(paragraph)) for paragraph in shape.iter(q('a', 'p')))
    if len(columns) != 2 or max(column_lines(shape) for shape in columns) <= ROADMAP_LINES:
        return
    for shape in columns:
        for run in shape.iter(q('a', 'rPr')):
            run.set('sz', str(tokens['sizes']['evidence'] * 100))


def finish(path: Path, tokens: dict) -> None:
    """Rewrite the deck in place; only slides with a table, a figure, a numbered list or the roadmap change."""
    colors = tokens['colors']
    temporary = path.with_name(f'.{path.name}.tmp')
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if SLIDE.fullmatch(item.filename) and (b'<a:tbl>' in data or b'<p:pic>' in data
                                                   or b'buAutoNum' in data or ROADMAP_TITLE.encode() in data
                                                   or tokens.get('code_font', '\0').encode() in data):
                xml = ET.fromstring(data)
                for table in xml.iter(q('a', 'tbl')):
                    format_table(table, colors)
                format_captions(xml, tokens)
                format_lists(xml, tokens)
                format_roadmap(xml, tokens)
                format_code(xml, tokens)
                data = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
            target.writestr(item, data)
    shutil.move(temporary, path)
