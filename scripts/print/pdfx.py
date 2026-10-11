"""Turn a print interior rendered by LaTeX into the PDF/X file IngramSpark asks for.

Two steps, both used by scripts/print/build.py:

- strip_transparency_groups: LuaTeX wraps every included figure in a form XObject with a transparency
  group (/Group <</S /Transparency>>), which PDF/X-1a and PDF/X-3 forbid. The groups are not isolated,
  not knockout, and everything inside them is opaque, so removing them changes nothing on the page.
  Any real transparency (an opacity below 1, a soft mask, a blend mode) stops the build instead.
- to_pdfx: Ghostscript's pdfwrite writes PDF/X-1a:2001 (IngramSpark's recommended setting) with the
  book's title, a CMYK output intent (Ghostscript's SWOP profile) and no annotations. The pages are
  already CMYK or gray when they reach it (print/book-print-*.tex and scripts/print/recolor.py), so
  it converts no colors; scripts/print/preflight.py checks the result.

Ghostscript (https://ghostscript.com, free under the AGPL) is found from --gs-bin, then GS_BIN, then
PATH, then C:\\Program Files\\gs\\gs*\\bin\\gswin64c.exe.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
from pathlib import Path

PDFX_VERSION = 1  # Ghostscript's -dPDFX: 1 = PDF/X-1a:2001, 3 = PDF/X-3:2002
PDFX_NAMES = {1: 'PDF/X-1a:2001', 3: 'PDF/X-3:2002'}


def find_ghostscript(explicit: str | None = None) -> str:
    candidates = [explicit, os.environ.get('GS_BIN'), shutil.which('gswin64c'), shutil.which('gs')]
    if os.name == 'nt':
        def version(path: str) -> tuple:
            match = re.search(r'gs(\d+)\.(\d+)\.(\d+)', path)
            return tuple(int(part) for part in match.groups()) if match else (0,)
        for root in (os.environ.get('ProgramFiles', r'C:\Program Files'), r'C:\Program Files'):
            candidates += sorted(glob.glob(os.path.join(root, 'gs', 'gs*', 'bin', 'gswin64c.exe')),
                                 key=version, reverse=True)
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise RuntimeError('Ghostscript not found. Install it from https://ghostscript.com/releases/ '
                       '(Windows: gs<version>w64.exe), or pass --gs-bin or set GS_BIN.')


def cmyk_profile(gs: str) -> Path:
    """Ghostscript's own CMYK output profile (Artifex CMYK SWOP Profile), next to its bin folder."""
    profile = Path(gs).resolve().parent.parent / 'iccprofiles' / 'default_cmyk.icc'
    if not profile.is_file():
        raise RuntimeError(f'Ghostscript CMYK profile not found: {profile}')
    return profile


def strip_transparency_groups(source: Path, target: Path) -> int:
    """Copy source to target without the transparency groups of its forms and pages; returns how many."""
    import fitz  # PyMuPDF
    doc = fitz.open(source)
    removed = 0
    for xref in range(1, doc.xref_length()):
        text = doc.xref_object(xref, compressed=True)
        for key in ('/SMask', '/BM', '/ca', '/CA'):
            for match in re.finditer(re.escape(key) + r'(?![\w])\s*(/?[\w.]+)', text):
                value = match.group(1)
                opaque = (value in ('/None',) if key == '/SMask' else value in ('/Normal', '/Compatible')
                          if key == '/BM' else float(value) >= 1)
                if not opaque:
                    raise ValueError(f'{source.name}: object {xref} uses transparency ({key} {value})')
        group = doc.xref_get_key(xref, 'Group')
        if group[0] == 'dict' and '/Transparency' in group[1]:
            if '/K true' in group[1] or '/I true' in group[1]:
                raise ValueError(f'{source.name}: object {xref} has an isolated or knockout group')
            doc.xref_set_key(xref, 'Group', 'null')
            removed += 1
        elif group[0] == 'xref':
            sub = int(group[1].split()[0])
            if '/Transparency' in doc.xref_object(sub, compressed=True):
                doc.xref_set_key(xref, 'Group', 'null')
                removed += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.save(target, garbage=3, deflate=True)
    return removed


def ps_string(text: str) -> str:
    """A PostScript string literal (Latin-1; the book's title is ASCII)."""
    escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    return '(' + escaped.encode('latin-1', 'replace').decode('latin-1') + ')'


def pdfx_definition(title: str, profile: Path, version: int = PDFX_VERSION) -> str:
    """The prefix file pdfwrite reads before the document: info keys, the ICC profile, the output intent
    (the pattern of Ghostscript's lib/PDFX_def.ps)."""
    return f'''%!
% Written by scripts/print/pdfx.py for Ghostscript's pdfwrite (-dPDFX={version}).
[ /GTS_PDFXVersion ({PDFX_NAMES[version]})
  /Title {ps_string(title)}
  /Trapped /False
/DOCINFO pdfmark

[/_objdef {{icc_PDFX}} /type /stream /OBJ pdfmark
[{{icc_PDFX}} << /N 4 >> /PUT pdfmark
[{{icc_PDFX}} ({profile.as_posix()}) (r) file /PUT pdfmark

[/_objdef {{OutputIntent_PDFX}} /type /dict /OBJ pdfmark
[{{OutputIntent_PDFX}} <<
  /Type /OutputIntent
  /S /GTS_PDFX
  /OutputCondition (Commercial and specialty printing)
  /Info (U.S. Web Coated \\(SWOP\\))
  /OutputConditionIdentifier (CGATS TR 001)
  /RegistryName (http://www.color.org)
  /DestOutputProfile {{icc_PDFX}}
>> /PUT pdfmark
[{{Catalog}} <</OutputIntents [ {{OutputIntent_PDFX}} ]>> /PUT pdfmark
'''


def to_pdfx(source: Path, target: Path, title: str, gs: str, work: Path,
            version: int = PDFX_VERSION) -> None:
    profile = cmyk_profile(gs)
    work.mkdir(parents=True, exist_ok=True)
    definition = work / 'PDFX_def.ps'
    definition.write_text(pdfx_definition(title, profile, version), encoding='latin-1')
    target.parent.mkdir(parents=True, exist_ok=True)
    args = [gs, f'-dPDFX={version}', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dQUIET',
            '-sDEVICE=pdfwrite',
            # The pages are CMYK or gray already; DeviceGray stays gray (it maps to black ink alone).
            '-sColorConversionStrategy=CMYK', '-sProcessColorModel=DeviceCMYK',
            '-dPreserveAnnots=false', '-dAutoRotatePages=/None',
            '-dEmbedAllFonts=true', '-dSubsetFonts=true',
            f'--permit-file-read={profile.as_posix()}',
            f'-sOutputFile={target}', str(definition), str(source)]
    print('+ ' + ' '.join(args), flush=True)
    result = subprocess.run(args, capture_output=True, text=True, errors='replace')
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or not target.is_file():
        raise RuntimeError(f'Ghostscript failed ({result.returncode}):\n{output}')
    if output:
        print(output, flush=True)
