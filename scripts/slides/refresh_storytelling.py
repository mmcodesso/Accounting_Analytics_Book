"""Supplemental Chapter 1 teaching views; explicit refresh opens a read-only database.

The original refresh.py and its artifact inventory remain independent. Normal
builds only check committed provenance. Diagram labels and relationship meanings
come from the canonical Draw.io files, with a separate presentation geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.slides.refresh import (_content_hash, _pin, sha256, _svg, _text,
                                    _rect, _line, BLUE, TEAL, AMBER, INK, GRAY, RULE, WHITE, TINT)
from shared.calculations.foundations import key_example

OUTPUT = Path('shared/generated/chapter-01/storytelling')
FIGURES = ('fig-01-01-analytics-continuum', 'fig-01-03-tools-workflow-mapping',
           'fig-01-04-charles-river-architecture', 'fig-01-05-o2c-process-flow',
           'fig-03-05-chart-of-accounts-table')
GENERATORS = ('scripts/slides/refresh_storytelling.py', 'scripts/slides/refresh.py',
              'shared/calculations/foundations.py', 'scripts/figures/ch01.py', 'scripts/figures/ch03.py')
INPUTS = ('shared/generated/chapter-01/facts.json',
          'shared/generated/chapter-01/source-trace.svg',
          'shared/generated/chapter-01/salesorder-focus.svg') + tuple(
    f'visuals/src/{figure}.drawio' for figure in FIGURES)
VIEWS = ('analytics-types', 'tools-workflow', 'architecture-overview',
         'architecture-operating', 'architecture-reference', 'o2c-forward', 'checked-credit',
         'source-trace-dated', 'salesorder-task')
FRAGMENTS = ('_key-task.qmd', '_key-response.qmd', '_source-fields.qmd',
             '_customer-response.qmd', '_account-focus.qmd', '_item-response.qmd',
             '_initial-response.qmd', '_model-update.qmd')
ASSETS = tuple(f'{view}.{ext}' for view in VIEWS for ext in ('svg', 'png')) + FRAGMENTS


def hashes(root: Path, names: tuple) -> dict:
    # These additional text inputs are not covered by the base slide hasher.
    # Git may convert their line endings between Windows authoring and Linux CI.
    return {name: hashlib.sha256((root / name).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
            if Path(name).suffix in {'.json', '.drawio'} else _content_hash(root / name)
            for name in names}


def check_fresh(root: Path, manifest: dict) -> list[str]:
    if (OUTPUT / 'facts.json').as_posix() not in manifest.get('public_assets', []):
        return []
    try:
        folder = root / OUTPUT
        facts = json.loads((folder / 'facts.json').read_text(encoding='utf-8'))
        errors = []
        if facts.get('schema_version') != 1 or facts.get('dataset') != _pin(root):
            errors.append('chapter-01 storytelling: dataset pin changed; run focused --refresh-shared')
        for key, names in [('generator_sha256', GENERATORS), ('input_sha256', INPUTS)]:
            if facts.get(key) != hashes(root, names):
                errors.append(f'chapter-01 storytelling: {key} changed; run focused --refresh-shared')
        if set(facts.get('artifact_sha256', {})) != set(ASSETS):
            errors.append('chapter-01 storytelling: incomplete artifact inventory')
        for name in ASSETS:
            path = folder / name
            if not path.is_file() or facts['artifact_sha256'].get(name) != _content_hash(path):
                errors.append(f'chapter-01 storytelling: missing or modified {name}')
        return errors
    except (OSError, KeyError, ValueError, TypeError) as exc:
        return [f'chapter-01 storytelling: cannot validate committed inputs: {exc}']


def cells(root: Path, figure: str) -> dict:
    return {cell.get('id'): cell for cell in ET.parse(root / f'visuals/src/{figure}.drawio').iter('mxCell')}


def label(cell: ET.Element, first: bool = True) -> str:
    text = re.sub(r'<br\s*/?>', '\n', cell.get('value', ''), flags=re.I)
    text = html.unescape(re.sub(r'<[^>]+>', '', text))
    return text.splitlines()[0] if first else text


def table(path: Path, headers: list, rows: list) -> None:
    def line(row): return '| ' + ' | '.join(str(v).replace('|', '\\|') for v in row) + ' |\n'
    path.write_text(line(headers) + line(['---'] * len(headers)) + ''.join(map(line, rows)), encoding='utf-8')


def box(out: list, x: int, y: int, w: int, title: str, detail: str = '', color=BLUE,
        min_height: int = 0) -> None:
    lines = [line for part in title.split('\n') for line in
             textwrap.wrap(part, width=max(10, (w-32)//19), break_long_words=False)]
    details = textwrap.wrap(detail, width=max(12, (w-32)//17), break_long_words=False)
    content_height = 18 + 36 * (len(lines) + len(details))
    height = max(content_height, min_height)
    offset = (height - content_height) // 2
    out.append(_rect(x, y, w, height, WHITE, color))
    for i, line in enumerate(lines):
        out.append(_text(x + 16, y + offset + 35 + i*36, line, 32, color, 'bold'))
    for i, line in enumerate(details):
        out.append(_text(x + 16, y + offset + 35 + (len(lines)+i)*36, line, 32, INK))


def link(out: list, x1, y1, x2, y2, *, dashed=False, color=AMBER) -> None:
    pattern = ' stroke-dasharray="10 7"' if dashed else ''
    out.append(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="3"{pattern}/>')
    length = math.hypot(x2-x1, y2-y1) or 1
    dx, dy = (x2-x1)/length, (y2-y1)/length
    ax, ay = x2-10*dx+6*dy, y2-10*dy-6*dx
    bx, by = x2-10*dx-6*dy, y2-10*dy+6*dx
    out.append(f'<path d="M{ax:g} {ay:g} L{x2} {y2} L{bx:g} {by:g}" fill="none" stroke="{color}" stroke-width="3"/>')


def architecture(root: Path, mode: str) -> str:
    source = cells(root, FIGURES[2]); out = []
    # Fail rather than silently reverse the book's established legend.
    posting = [c for c in source.values() if c.get('edge') == '1' and 'dashed=1' in c.get('style', '')]
    if not posting or label(source['c43']) != 'Posts to the general ledger' or label(source['c47']) != 'Shared keys':
        raise ValueError('Canonical architecture legend changed; review the focused views')
    operating = [('c1', 'SalesInvoice, Shipment'), ('c7', 'PurchaseInvoice, payments'),
                 ('c10', 'WorkOrder, completions'), ('c13', 'PayrollRegister, payments')]
    reference = [('c16', 'FixedAsset, DebtAgreement'), ('c19', 'ItemID, EmployeeID'),
                 ('c22', 'CostCenterID, AccountID'), ('c25', 'ItemID')]
    if mode == 'overview':
        row_height, row_pitch, top = 90, 100, 15
        centers = [top + i*row_pitch + row_height//2 for i in range(4)]
        core_center = (centers[0] + centers[-1]) // 2
        for i, (key, _) in enumerate(operating):
            box(out, 15, top+i*row_pitch, 335, label(source[key]), color=TEAL, min_height=row_height)
        box(out, 425, core_center-row_height//2, 330, label(source['c28']), min_height=row_height)
        for i, (key, _) in enumerate(reference):
            box(out, 850, top+i*row_pitch, 415, label(source[key]), min_height=row_height)
        for y in centers: link(out, 350, y, 425, core_center, dashed=True)
        for i, y in enumerate(centers):
            link(out, 850, y, 755, core_center, dashed=i == 0)
        out.append(_text(15, 440, 'Design Services belongs within Order-to-Cash.', 32, INK))
    else:
        entries = operating if mode == 'operating' else reference
        for i, (key, detail) in enumerate(entries):
            box(out, 20, 10+i*96, 540, label(source[key]), detail, TEAL if mode == 'operating' else BLUE)
            link(out, 560, 51+i*96, 780, 198, dashed=mode == 'operating' or i == 0)
        box(out, 790, 160, 475, label(source['c28']), 'Account, JournalEntry, GLEntry')
        if mode == 'operating':
            out.append(_text(790, 310, 'Accounting evidence', 32, INK))
        else:
            out.append(_text(790, 310, 'Context through shared keys', 32, INK))
    link(out, 20, 465, 90, 465, dashed=True)
    out.append(_text(110, 474, 'Dashed: ledger posting', 32, INK))
    link(out, 650, 465, 720, 465)
    out.append(_text(740, 474, 'Solid: shared key', 32, INK))
    return _svg('Charles River architecture', 'Focused adaptation of Figure 1.4. Dashed links are postings and solid links are shared keys.', out, height=500)


def process(root: Path, trace: dict, checked=False) -> str:
    source = cells(root, FIGURES[3]); out = []
    if checked:
        box(out, 20, 45, 380, f"SalesInvoice {trace['invoice_id']}", f"Line {trace['invoice_line_id']}", BLUE)
        box(out, 790, 45, 475, f"GLEntry {trace['gl_entry_id']}", f"Credit ${trace['credit']:,.2f}", TEAL)
        link(out, 400, 86, 785, 86, dashed=True, color=TEAL)
        out.append(_text(422, 170, 'Only this revenue credit checked', 32, TEAL, 'bold'))
        out.append(_text(20, 242, 'Other postings, cash, and applications require separate checks.', 32, INK))
        out.append(_text(20, 312, 'One amount agreement does not verify the entire sale.', 32, INK))
        out.append(_text(20, 390, 'Navigation example: 5 March 2025', 32, GRAY))
    else:
        for i, key in enumerate(('c1','c2','c3','c4','c5','c6','c7','c8')):
            x = 20+(i%4)*318; y = 20+(i//4)*150
            title=label(source[key]); detail=label(source[key], False).splitlines()[1]
            if key=='c8': title='CashReceipt\nApplication'; detail='to invoices'
            elif key=='c4': detail='product, cost'
            elif key=='c5': detail='ship date, carrier'
            elif key=='c6': detail='invoice date, total'
            elif key=='c7': detail='receipt date, amount'
            elif key=='c2': detail='customer, date'
            elif key=='c3': detail='item, quantity'
            box(out,x,y,300,title,detail,TEAL if key!='c4' else BLUE)
        for x in (320,638): link(out,x,61,x+15,61,color=GRAY)
        # Item is a master reference. The goods sequence continues at Shipment.
        link(out, 974, 61, 959, 61, color=AMBER)
        out.append(f'<path d="M 805 110 V 142 H 160 V 145" fill="none" stroke="{GRAY}" stroke-width="3"/>')
        link(out,160,145,160,165,color=GRAY)
        for x in (320,638,956): link(out,x,211,x+15,211,color=GRAY)
        box(out,20,320,1245,label(source['c9']),'Shipment: inventory/COGS; invoice: revenue/AR; receipts: cash; applications: AR',BLUE)
        for x in (160,478,796,1114): link(out,x,295,x,315,dashed=True)
        out.append(_text(20,485,'Gray: sequence    Dashed amber: posting    Solid amber: master key',32,INK))
    return _svg('One checked revenue credit' if checked else 'Order-to-Cash goods process',
                'Adapted from Figure 1.5. The goods sequence does not describe every service invoice.',out,height=500 if checked else 520)


def teaching_maps(root: Path) -> dict:
    source=cells(root,FIGURES[0]); out=[]
    for i, key in enumerate(('c1','c3','c5','c7')):
        parts=label(source[key],False).splitlines(); x=15+i*318
        out.append(_rect(x,90,302,235,TINT,RULE))
        for j, word in enumerate(parts[0].split()): out.append(_text(x+15,135+j*36,word,32,BLUE,'bold'))
        for j, line in enumerate(textwrap.wrap(parts[1].strip('"'), width=16)):
            out.append(_text(x+15,245+j*42,line,32,INK))
    out.append(_text(15,405,'A single investigation can ask several kinds of question.',32,INK))
    continuum=_svg('Four types of analytics','Figure 1.1, with teaching-sized labels.',out,height=470)
    source=cells(root,FIGURES[1]);out=[]
    for i in range(6):
        x=5+i*212
        out.append(_text(x+5,32,label(source[f'c{i+1}']).split('. ',1)[1],32,BLUE,'bold'))
    # The book mapping emphasizes common use, not exclusive capabilities.
    for y,key,start,width in [(70,'c12',1,3),(160,'c15',2,2),(250,'c18',3,2)]:
        parts=label(source[key],False).splitlines();x=10+start*212
        out.append(_rect(x,y,width*212-12,80,TINT,RULE))
        out.append(_text(x+12,y+32,parts[0],32,BLUE,'bold'))
        # Long SQL explanation stays in narration, while the tool bar conveys stages.
        out.append(_text(x+12,y+64,'Common teaching use',32,INK))
        out.append(_text(1070,y+43,'Communicate',32,TEAL,'bold'))
    return {'analytics-types':continuum,'tools-workflow':_svg('Tools across the workflow','Figure 1.3 mapping, with overlapping capabilities and communication across every tool.',out,height=335)}


def existing_views(root: Path) -> dict:
    """Keep the strong existing views while withholding the lookup response."""
    namespace='{http://www.w3.org/2000/svg}'
    trace=ET.parse(root/INPUTS[1]).getroot()
    trace.find(namespace+'title').text='Navigation example: 5 March 2025'
    # Native SVG banner uses existing whitespace above the evidence panels.
    group=trace.find(namespace+'g')
    for child in list(group):
        if child.tag == namespace+'text' and child.get('y') == '52':
            group.remove(child)
    banner=ET.fromstring(_text(32,42,'5 March 2025: one posting, separate from the 2026 comparison',32,BLUE,'bold'))
    banner.tag=namespace+'text';group.insert(0,banner)
    order=ET.parse(root/INPUTS[2]).getroot()
    order.set('viewBox','0 0 1280 360');order.set('height','360')
    order.find(namespace+'desc').text='SalesOrder worksheet mock: first three rows, with CustomerID highlighted for lookup. The customer name appears on the separate response slide.'
    group=order.find(namespace+'g')
    for child in list(group):
        if float(child.get('y','0'))>=350 or child.tag.endswith('path'):
            group.remove(child)
    for element in group.iter(namespace+'text'):
        if element.get('font-size')=='32':element.set('font-size','34')
    return {'source-trace-dated':ET.tostring(trace,encoding='unicode'),
            'salesorder-task':ET.tostring(order,encoding='unicode')}


def refresh(root: Path) -> None:
    root=root.resolve(); pin=_pin(root)
    database=(Path(os.environ.get('CHARLESRIVER_DATA',root/'datasets'))/'CharlesRiver.sqlite').resolve()
    before=sha256(database)
    if before != pin['sha256']: raise ValueError('Pinned dataset checksum mismatch')
    renderer=os.environ.get('RSVG_CONVERT') or shutil.which('rsvg-convert')
    if not renderer: raise RuntimeError('rsvg-convert is required for explicit storytelling refresh')
    base=json.loads((root/INPUTS[0]).read_text(encoding='utf-8'))
    db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    try:
        keys=key_example(db)
        account=db.execute('SELECT AccountID,AccountNumber,AccountName,ParentAccountID FROM Account WHERE AccountID IN (41,42) ORDER BY AccountID').fetchall()
        items=db.execute("SELECT ItemID,ItemName,SupplyMode,StandardCost FROM Item WHERE ItemGroup='Furniture' AND ItemID IN (SELECT MIN(ItemID) FROM Item WHERE ItemGroup='Furniture' GROUP BY SupplyMode) ORDER BY ItemID").fetchall()
        customer=db.execute('SELECT so.SalesOrderID,so.CustomerID,c.CustomerName FROM SalesOrder so JOIN Customer c ON c.CustomerID=so.CustomerID WHERE so.SalesOrderID=1').fetchone()
    finally: db.close()
    if sha256(database)!=before: raise RuntimeError('Dataset changed during read-only refresh')
    if list(customer)!=[1,81,'Koch-Ali'] or [r[0] for r in account]!=[41,42]:
        raise ValueError('Approved navigation examples changed; editorial review required')
    folder=root/OUTPUT;folder.mkdir(parents=True,exist_ok=True)
    maps=teaching_maps(root)
    maps.update(existing_views(root))
    maps.update({f'architecture-{mode}':architecture(root,mode) for mode in ('overview','operating','reference')})
    maps['o2c-forward']=process(root,base['source_trace'])
    maps['checked-credit']=process(root,base['source_trace'],True)
    for name, document in maps.items():
        ET.fromstring(document);path=folder/(name+'.svg');path.write_text(document,encoding='utf-8')
        subprocess.run([renderer,'--width','2560','--output',str(folder/(name+'.png')),str(path)],check=True)
    table(folder/'_key-task.qmd',['SalesOrderID','CustomerID'],[[r[0],r[2]] for r in keys['orders']])
    names={r[0]:r[1] for r in keys['customers']}
    table(folder/'_key-response.qmd',['SalesOrderID','CustomerID','CustomerName'],[[r[0],r[2],names[r[2]]] for r in keys['orders']])
    trace=base['source_trace']
    table(folder/'_source-fields.qmd',['Field in GLEntry','Value','Record to locate'],[
        ['SourceDocumentType',trace['source_type'],'SalesInvoice table'],
        ['SourceDocumentID',trace['invoice_id'],'SalesInvoiceID'],
        ['SourceLineID',trace['invoice_line_id'],'SalesInvoiceLineID']])
    table(folder/'_customer-response.qmd',['SalesOrderID','CustomerID','CustomerName'],[customer])
    table(folder/'_account-focus.qmd',['AccountID','AccountNumber','AccountName','ParentAccountID'],[[*r[:3],r[3] or '—'] for r in account])
    table(folder/'_item-response.qmd',['ItemID','SupplyMode','StandardCost'],[[r[0],r[2],f'${r[3]:,.2f}'] for r in items])
    q3,q4=base['furniture_quarters'][2:];change=(q3['margin_rate']-q4['margin_rate'])*100
    (folder/'_initial-response.qmd').write_text(f"**Observation:** Furniture's margin rate fell from {q3['margin_rate']:.2%} to {q4['margin_rate']:.2%}, about **{change:.2f} percentage points**.\n\n**Qualification:** Fiscal 2026 invoice lines, valued at item standard cost.\n\n**Next evidence:** Invoice detail and item records to investigate the change.\n",encoding='utf-8')
    (folder/'_model-update.qmd').write_text(f"Furniture's invoice-based margin at standard cost fell from **{q3['margin_rate']:.2%} in Q3** to **{q4['margin_rate']:.2%} in Q4 2026**, about **{change:.2f} percentage points**.\n\nWe need transaction detail to explain the change and a separate ledger reconciliation to assess financial-statement gross profit.\n\nThe **5 March 2025** example verifies one invoice line against one revenue credit. It teaches navigation and provides no explanation for the 2026 decline.\n",encoding='utf-8')
    facts={'schema_version':1,'dataset':pin,'generator_sha256':hashes(root,GENERATORS),
           'input_sha256':hashes(root,INPUTS),'artifact_sha256':hashes(folder,ASSETS),
           'key_example':keys,'customer_lookup':list(customer),'account_rows':account,
           'item_rows':items,'margin_change_percentage_points':change,
           'text_hash_policy':'UTF-8 normalized LF; dataset and PNG use raw bytes'}
    (folder/'facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Refreshed Chapter 1 storytelling views; dataset SHA-256 unchanged ({before}).')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0]);parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:
        errors=check_fresh(ROOT,{'public_assets':[(OUTPUT/'facts.json').as_posix()]})
        for error in errors: print(error,file=sys.stderr)
        raise SystemExit(bool(errors))
    refresh(ROOT)
