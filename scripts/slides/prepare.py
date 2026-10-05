"""Prepare disposable shared slide inputs, never the dataset or chapter prose."""
from __future__ import annotations

import os
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .verify import load_manifest, safe_path

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS = {'a': A, 'p': P}
ET.register_namespace('a', A)
ET.register_namespace('p', P)
ET.register_namespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
LAYOUTS = {'Title Slide', 'Title and Content', 'Section Header', 'Two Content',
           'Comparison', 'Content with Caption', 'Blank'}
EMU = 914400


def find_quarto() -> str:
    candidates = [os.environ.get('QUARTO_BIN'), shutil.which('quarto')]
    if os.name == 'nt':
        candidates += [str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Quarto/bin/quarto.exe'),
                       r'C:\Program Files\Quarto\bin\quarto.exe']
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise RuntimeError('Quarto not found. Install the pinned version or set QUARTO_BIN.')


def reset_owned(root: Path, path: Path) -> None:
    """Only clear explicitly designated generated directories within this checkout."""
    resolved, base = path.resolve(), root.resolve()
    allowed = [base / 'slides/_shared', base / 'slides/_build', base / 'outputs/build']
    if not any(resolved == item or resolved.is_relative_to(item) for item in allowed):
        raise ValueError(f'Refusing to clear non-build directory: {resolved}')
    if path.is_symlink():
        raise ValueError(f'Refusing to clear symlink: {path}')
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _xfrm(sp: ET.Element, box: tuple[float, float, float, float]) -> None:
    properties = sp.find('p:spPr', NS)
    if properties is None:
        properties = ET.SubElement(sp, f'{{{P}}}spPr')
    previous = properties.find('a:xfrm', NS)
    if previous is not None:
        properties.remove(previous)
    transform = ET.SubElement(properties, f'{{{A}}}xfrm')
    x, y, w, h = (str(round(value * EMU)) for value in box)
    ET.SubElement(transform, f'{{{A}}}off', x=x, y=y)
    ET.SubElement(transform, f'{{{A}}}ext', cx=w, cy=h)


def theme_reference(source: Path, target: Path, tokens: dict, *, set_geometry: bool = False) -> None:
    """Theme Pandoc masters using native placeholders and an explicit 16:9 grid."""
    colors, sizes = tokens['colors'], tokens['sizes']
    replacements = {'dk1': 'ink', 'lt1': 'paper', 'dk2': 'blue', 'lt2': 'tint',
                    'accent1': 'blue', 'accent2': 'teal', 'accent3': 'gray',
                    'accent4': 'coral', 'accent5': 'amber', 'accent6': 'blue',
                    'hlink': 'blue', 'folHlink': 'teal'}
    found = set()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as out:
        for name in src.namelist():
            data = src.read(name)
            if name.startswith('ppt/') and name.endswith('.xml'):
                xml = ET.fromstring(data)
                if name == 'ppt/presentation.xml':
                    size = xml.find('p:sldSz', NS)
                    size.set('cx', str(round(13.333333 * EMU)))
                    size.set('cy', str(round(7.5 * EMU)))
                    size.set('type', 'screen16x9')
                if name.startswith('ppt/theme/'):
                    scheme = xml.find('.//a:clrScheme', NS)
                    if scheme is not None:
                        for slot in scheme:
                            role = replacements.get(slot.tag.split('}')[-1])
                            if role:
                                for child in list(slot): slot.remove(child)
                                ET.SubElement(slot, f'{{{A}}}srgbClr', val=colors[role])
                    for latin in xml.findall('.//a:fontScheme//a:latin', NS):
                        latin.set('typeface', tokens['font'])
                for default in xml.findall('.//a:defRPr', NS):
                    default.set('sz', str(sizes['body'] * 100))
                for font in xml.findall('.//a:latin', NS):
                    font.set('typeface', tokens['font'])
                for style_name, role in [('titleStyle', 'title'), ('bodyStyle', 'body'), ('otherStyle', 'body')]:
                    for prop in xml.findall(f'.//p:{style_name}//a:defRPr', NS):
                        prop.set('sz', str(sizes[role] * 100))
                        prop.attrib.pop('cap', None)
                        if role == 'title':
                            prop.set('b', '1')
                            for fill in prop.findall('a:solidFill', NS): prop.remove(fill)
                            fill = ET.SubElement(prop, f'{{{A}}}solidFill')
                            ET.SubElement(fill, f'{{{A}}}schemeClr', val='accent1')
                    for paragraph in xml.findall(f'.//p:{style_name}/*', NS):
                        paragraph.set('algn', 'l')
                if name.startswith('ppt/slideLayouts/'):
                    common = xml.find('p:cSld', NS)
                    layout = common.get('name', '') if common is not None else ''
                    found.add(layout)
                    for sp in xml.findall('.//p:sp', NS):
                        ph = sp.find('p:nvSpPr/p:nvPr/p:ph', NS)
                        if ph is None: continue
                        kind, idx = ph.get('type', 'obj'), int(ph.get('idx', '0'))
                        role = 'body'
                        if kind in {'title', 'ctrTitle'}:
                            role = 'opening' if layout in {'Title Slide', 'Section Header'} else 'title'
                            box = (0.65, 1.35, 12.0, 2.0) if layout == 'Title Slide' else (0.65, 0.45, 12.0, 1.0)
                            if layout == 'Section Header': box = (0.65, 2.0, 12.0, 1.8)
                        elif kind == 'subTitle': box = (0.65, 3.65, 12.0, 2.0)
                        elif kind in {'dt', 'ftr', 'sldNum'}:
                            role = 'attribution'
                            box = (0.65, 7.0, 12.0, 0.25)
                        elif layout == 'Two Content':
                            is_right = idx == 2
                            box = (6.9 if is_right else 0.65, 2.25, 5.75, 4.35)
                        elif layout == 'Comparison':
                            is_right = idx in {3, 4}
                            caption = idx in {1, 3}
                            box = (6.9 if is_right else 0.65,
                                   1.65 if caption else 3.05, 5.75,
                                   1.35 if caption else 3.65)
                        elif layout == 'Content with Caption':
                            # A full-width caption above the evidence avoids squeezing
                            # accounting field names into a narrow table column.
                            box = (0.65, 1.65, 12.0, 1.35) if kind == 'body' else (0.65, 3.05, 12.0, 3.65)
                        else: box = (0.65, 1.65, 12.0, 5.05)
                        if set_geometry:
                            _xfrm(sp, box)
                        body = sp.find('p:txBody', NS)
                        if body is not None:
                            props = body.find('a:bodyPr', NS)
                            if props is not None and set_geometry:
                                centered = (layout == 'Title and Content'
                                            and kind not in {'title', 'ctrTitle', 'dt', 'ftr', 'sldNum'})
                                props.set('anchor', 'ctr' if centered else 't')
                            style = body.find('a:lstStyle', NS)
                            if style is None: style = ET.SubElement(body, f'{{{A}}}lstStyle')
                            paragraph = style.find('a:lvl1pPr', NS)
                            if paragraph is None: paragraph = ET.SubElement(style, f'{{{A}}}lvl1pPr')
                            paragraph.set('algn', 'l')
                            if (set_geometry and layout in {'Title and Content', 'Two Content'}
                                    and kind not in {'title', 'ctrTitle', 'dt', 'ftr', 'sldNum'}):
                                for spacing in paragraph.findall('a:spcAft', NS): paragraph.remove(spacing)
                                spacing = ET.Element(f'{{{A}}}spcAft')
                                ET.SubElement(spacing, f'{{{A}}}spcPts', val='1200')
                                paragraph.insert(0, spacing)
                            prop = paragraph.find('a:defRPr', NS)
                            if prop is None: prop = ET.SubElement(paragraph, f'{{{A}}}defRPr')
                            prop.set('sz', str(sizes[role] * 100))
                            prop.attrib.pop('cap', None)
                            if role in {'title', 'opening'}:
                                prop.set('b', '1')
                                for fill in prop.findall('a:solidFill', NS): prop.remove(fill)
                                fill = ET.SubElement(prop, f'{{{A}}}solidFill')
                                ET.SubElement(fill, f'{{{A}}}schemeClr', val='accent1')
                            for paragraph in body.findall('a:p/a:pPr', NS): paragraph.set('algn', 'l')
                        for prop in sp.findall('.//a:defRPr', NS) + sp.findall('.//a:rPr', NS):
                            prop.set('sz', str(sizes[role] * 100))
                            prop.attrib.pop('cap', None)
                data = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
            out.writestr(name, data)
    missing = LAYOUTS - found
    if missing: raise ValueError(f'Reference template lacks layouts: {sorted(missing)}')


def prepare(root: Path, manifest: dict) -> None:
    stage = root / 'slides/_shared'
    reset_owned(root, stage)
    for rel in manifest.get('public_assets', []) + manifest.get('public_fragments', []):
        source = safe_path(root, rel, public=True)
        if not source.is_file(): raise ValueError(f'Missing public input: {rel}')
        # A predictable mirror below _shared; definitions have no path assumptions.
        relative = Path(rel).relative_to('shared') if rel.startswith('shared/') else Path(rel)
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    # Public examples are formatted once for prose, tables, charts, and notes.
    # JSON is valid YAML and preserves currency strings without float surprises.
    variables = load_manifest(root / '_variables.yml')
    facts_file = root / 'shared/generated/chapter-01/facts.json'
    if facts_file.is_file():
        facts = json.loads(facts_file.read_text(encoding='utf-8'))
        trace = dict(facts['source_trace'])
        for field in ('unit_price', 'credit', 'debit', 'line_total'):
            trace[field] = f'${trace[field]:,.2f}'
        trace['quantity'] = f'{trace["quantity"]:g}'
        variables['slide'] = {'trace': trace}
    for chapter in manifest.get('chapters', []):
        facts_path = root / 'shared/generated' / chapter['id'] / 'facts.json'
        if facts_path.is_file():
            facts = json.loads(facts_path.read_text(encoding='utf-8'))
            if 'variables' in facts:
                variables.setdefault('slide', {})[chapter['id'].replace('-', '')] = facts['variables']
    (root / 'slides/_variables.yml').write_text(json.dumps(variables, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tokens = load_manifest(root / 'slides/theme/tokens.yml')
    colors, sizes = tokens['colors'], tokens['sizes']
    theme = stage / 'theme'
    theme.mkdir(parents=True, exist_ok=True)
    scss = '\n'.join(['/*-- scss:defaults --*/',
        f'$font-family-sans-serif: "{tokens["font"]}", "{tokens["fallback_font"]}", sans-serif;',
        f'$font-family-monospace: "{tokens["code_font"]}", monospace;',
        f'$body-color: #{colors["ink"]};', f'$body-bg: #{colors["paper"]};',
        f'$link-color: #{colors["blue"]};', f'$presentation-heading-color: #{colors["blue"]};',
        f'$presentation-font-size-root: {sizes["body"] * 4 / 3:g}px;',
        '/*-- scss:rules --*/',
        f'.reveal h1 {{ font-size: {sizes["opening"] * 4 / 3:g}px; }}',
        f'.reveal h2 {{ font-size: {sizes["title"] * 4 / 3:g}px; }}', ''])
    (theme / 'tokens.scss').write_text(scss, encoding='utf-8')
    # Pandoc's PPTX code font is a document variable, not a master placeholder.
    # Derive it from the same token used by Reveal instead of accepting Courier.
    (theme / 'metadata.yml').write_text(json.dumps({'monofont': tokens['code_font']}) + '\n', encoding='utf-8')
    theme_reference(root / 'slides/theme/reference-base.pptx', theme / 'reference.pptx', tokens)


def initialize_reference(root: Path, quarto: str) -> None:
    """One-time bootstrap. Ordinary builds require the committed reference base."""
    target = root / 'slides/theme/reference-base.pptx'
    if target.exists(): raise ValueError('Reference base already exists; refusing to overwrite it')
    default = root / 'outputs/build/reference-default.pptx'
    default.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([quarto, 'pandoc', '-o', str(default), '--print-default-data-file', 'reference.pptx'],
                   cwd=root, check=True)
    theme_reference(default, target, load_manifest(root / 'slides/theme/tokens.yml'), set_geometry=True)
