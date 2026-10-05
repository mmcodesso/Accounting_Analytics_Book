"""Dataset-free provenance checks and explicit read-only refresh for Chapters 2–3."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.calculations.foundations import budget_example, key_example, quality_examples, relationship, sale_trace
from scripts.slides.refresh import (_content_hash, _pin, _line, _rect, _svg, _text,
                                    sha256, BLUE, TEAL, AMBER, INK, GRAY, RULE, TINT, WHITE)

GENERATORS = ('shared/calculations/foundations.py', 'scripts/slides/refresh_foundations.py',
              'scripts/slides/refresh.py')
ASSETS = {
    'chapter-02': ('freight-comparison.svg', 'freight-comparison.png', '_missing.qmd',
                   '_status.qmd', '_duplicates.qmd', '_budget-wide.qmd', '_budget-long.qmd'),
    'chapter-03': ('customer-orders.svg', 'customer-orders.png', 'order-lines.svg', 'order-lines.png',
                   'shipment-invoice.svg', 'shipment-invoice.png', 'cash-applications.svg',
                   'cash-applications.png', 'account-ledger.svg', 'account-ledger.png',
                   'work-order-close.svg', 'work-order-close.png', 'crow-foot.svg', 'crow-foot.png',
                   '_keys.qmd', '_invoice-postings.qmd', '_shipment-postings.qmd', '_invoice-parts.qmd'),
}
RELATIONS = {
    'customer-orders': ('Customer', 'CustomerID', 'SalesOrder', 'CustomerID'),
    'order-lines': ('SalesOrder', 'SalesOrderID', 'SalesOrderLine', 'SalesOrderID'),
    'item-lines': ('Item', 'ItemID', 'SalesOrderLine', 'ItemID'),
    'shipment-invoice': ('ShipmentLine', 'ShipmentLineID', 'SalesInvoiceLine', 'ShipmentLineID'),
    'cash-applications': ('CashReceipt', 'CashReceiptID', 'CashReceiptApplication', 'CashReceiptID'),
    'invoice-applications': ('SalesInvoice', 'SalesInvoiceID', 'CashReceiptApplication', 'SalesInvoiceID'),
    'account-ledger': ('Account', 'AccountID', 'GLEntry', 'AccountID'),
    'work-order-close': ('WorkOrder', 'WorkOrderID', 'WorkOrderClose', 'WorkOrderID'),
}
MEANINGS = {'ERmandOne':'exactly one', 'ERzeroToOne':'zero or one',
            'ERzeroToMany':'zero or many', 'ERoneToMany':'one or many'}


def check_fresh(root: Path, manifest: dict) -> list[str]:
    errors = []
    for chapter, assets in ASSETS.items():
        rel = f'shared/generated/{chapter}/facts.json'
        if rel not in manifest.get('public_assets', []): continue
        try:
            folder = root / 'shared/generated' / chapter
            facts = json.loads((root/rel).read_text(encoding='utf-8'))
            if facts.get('schema_version') != 1 or facts.get('dataset') != _pin(root):
                errors.append(f'{chapter}: dataset pin changed; run --refresh-shared')
            if facts.get('generator_sha256') != {n:_content_hash(root/n) for n in GENERATORS}:
                errors.append(f'{chapter}: shared source changed; run --refresh-shared')
            if set(facts.get('artifact_sha256', {})) != set(assets):
                errors.append(f'{chapter}: incomplete generated artifact inventory')
            for name in assets:
                if not (folder/name).is_file() or facts['artifact_sha256'].get(name) != _content_hash(folder/name):
                    errors.append(f'{chapter}: missing or modified generated artifact {name}')
        except (OSError, KeyError, ValueError, TypeError) as exc:
            errors.append(f'{chapter}: cannot validate public facts: {exc}')
    return errors


def table(path: Path, headers: list[str], rows: list) -> None:
    def cell(value): return str(value).replace('|', '\\|')
    lines = ['| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |']
    lines += ['| '+' | '.join(cell(v) for v in row)+' |' for row in rows]
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def endpoint(x: int, y: int, inward: int, kind: str, color: str = GRAY) -> list[str]:
    """Crow's-foot endpoint at the table edge, extending into the connecting line."""
    out = []
    if kind in ('ERoneToMany','ERzeroToMany'):
        for dy in (-15, 0, 15): out.append(_line(x,y+dy,x+inward*27,y,color))
    else:
        out.append(_line(x+inward*10,y-15,x+inward*10,y+15,color))
    if kind in ('ERzeroToOne','ERzeroToMany'):
        out.append(f'<circle cx="{x+inward*43}" cy="{y}" r="10" fill="white" stroke="{color}" stroke-width="3"/>')
    else:
        out.append(_line(x+inward*43,y-15,x+inward*43,y+15,color))
    return out


def node(name: str, x: int, y: int, fields: list[str], group: str = '') -> list[str]:
    width, height = 460, 68 + len(fields)*49
    color = GRAY if group == 'Master Data' else BLUE
    out = [_rect(x,y,width,height,WHITE,RULE,0), _rect(x,y,width,58,color,color,0),
           _text(x+18,y+39,name,33,WHITE,'bold')]
    out += [_text(x+18,y+99+i*49,line,32) for i,line in enumerate(fields)]
    if group: out.append(_text(x,y-16,group,28,GRAY))
    return out


def pair(name: str, rel: tuple, markers: tuple, fields: tuple[list, list]) -> str:
    parent, pk, child, fk = rel
    out = node(parent,30,100,fields[0]) + node(child,790,100,fields[1])
    out += [_line(490,209,790,209), *endpoint(490,209,1,markers[0]), *endpoint(790,209,-1,markers[1])]
    out += [_text(640,330,f'{parent}: {MEANINGS[markers[0]]}',32,INK,anchor='middle'),
            _text(640,382,f'{child}: {MEANINGS[markers[1]]}',32,INK,anchor='middle'),
            _text(640,463,'Read each endpoint as matches in the table it touches.',30,GRAY,anchor='middle')]
    return _svg(name, f'{parent}.{pk} matches {child}.{fk}. The {parent} end is '
        f'{MEANINGS[markers[0]]}; the {child} end is {MEANINGS[markers[1]]}. '
        'Logical relationship, with endpoints computed from the pinned data.',out,height=500)


def junction(name: str, relations: list[tuple], markers: list[tuple], middle_fields: list[str]) -> str:
    top, bottom = relations
    child = top[2]
    out = node(top[0],30,35,[f'PK  {top[1]}']) + node(bottom[0],30,343,[f'PK  {bottom[1]}'],
        group='Master Data' if bottom[0]=='Item' else '')
    out += node(child,790,165,middle_fields)
    for rel, ends, y, cy in [(top,markers[0],130,313),(bottom,markers[1],438,362)]:
        color = AMBER if rel[0]=='Item' else GRAY
        out += [_line(490,y,640,y,color), _line(640,y,640,cy,color), _line(640,cy,790,cy,color)]
        out += endpoint(490,y,1,ends[0],color) + endpoint(790,cy,-1,ends[1],color)
        count = {'ERmandOne':'1','ERzeroToOne':'0–1','ERzeroToMany':'0+','ERoneToMany':'1+'}[ends[1]]
        out.append(_text(510,y-28,count + (' lines' if child=='SalesOrderLine' else ' applications'),32,color))
    out.append(_text(640,552,'Each junction row records one association and its own amount or quantity.',30,GRAY,anchor='middle'))
    return _svg(name,'Two parent tables connect to a junction table. '+
        ' '.join(f'{r[0]} to {r[2]}: {MEANINGS[m[0]]} at parent and {MEANINGS[m[1]]} at child.'
                 for r,m in zip(relations,markers)),out,height=580)


def notation() -> str:
    out=[]
    for i,kind in enumerate(MEANINGS):
        y=70+i*118
        out += [_line(80,y,440,y), *endpoint(440,y,-1,kind),
                _text(520,y+11,MEANINGS[kind].capitalize(),36,BLUE,'bold')]
    out.append(_text(640,539,'Circle = optional   |   Bar = one   |   Crow\'s foot = many',32,GRAY,anchor='middle'))
    return _svg("Crow's-foot notation",'Four endpoint symbols: exactly one, zero or one, zero or many, one or many.',out,height=580)


def freight_svg(examples: dict) -> str:
    average, largest = examples['freight_summary']
    out = [_text(32,47,'Shipment freight cost',34,BLUE,'bold')]
    for i,(label,value) in enumerate([('Mean of all shipments',average),('Largest recorded cost',largest)]):
        y=140+i*165
        out += [_text(32,y,label,32), _rect(440,y-40,650*value/largest,62,TINT,BLUE,0),
                _text(1125,y+2,f'${value:,.2f}',32,BLUE,'bold')]
    out += [_text(440,427,'0',30,GRAY),_text(1080,427,f'${largest:,.0f}',30,GRAY,'normal','end'),
            _text(32,505,'Unusual magnitude identifies a question to investigate.',34,TEAL,'bold')]
    return _svg('Shipment freight outlier in context',f'Mean freight cost ${average:,.2f}; '
                f'largest ${largest:,.2f}. Bars start at zero. Neither magnitude nor this comparison proves an error.',out,height=545)


def refresh(root: Path) -> None:
    root=root.resolve(); pin=_pin(root)
    database=(Path(os.environ.get('CHARLESRIVER_DATA',root/'datasets'))/'CharlesRiver.sqlite').resolve()
    before=sha256(database)
    if before != pin['sha256']: raise ValueError('Pinned dataset checksum mismatch')
    renderer=os.environ.get('RSVG_CONVERT') or shutil.which('rsvg-convert')
    if not renderer: raise RuntimeError('rsvg-convert is required for explicit shared refresh')
    db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    try:
        quality=quality_examples(db); budgets=budget_example(db); keys=key_example(db); trace=sale_trace(db)
        markers={name:relationship(db,*rel) for name,rel in RELATIONS.items()}
        parts=db.execute('SELECT SubTotal, FreightAmount, TaxAmount, GrandTotal FROM SalesInvoice WHERE SalesInvoiceID=?',(trace['inv'][0],)).fetchone()
        paid=db.execute('SELECT COUNT(DISTINCT SalesInvoiceID) FROM CashReceiptApplication WHERE CashReceiptID=?',(trace['app'][1],)).fetchone()[0]
    finally: db.close()
    if sha256(database)!=before: raise RuntimeError('Dataset changed during read-only refresh')
    money=lambda n:f'${n:,.2f}'
    folders={c:root/'shared/generated'/c for c in ASSETS}
    for folder in folders.values(): folder.mkdir(parents=True,exist_ok=True)
    c2,c3=folders.values()
    table(c2/'_missing.qmd',['Shipment','Shipment date','Tracking number'],[[r[0],r[1],r[3] or '(blank)'] for r in quality['missing']])
    table(c2/'_status.qmd',['Shipment','Status','Delivery date'],[[r[0],r[2],r[3]] for r in quality['status']])
    repeated=[r for r in quality['duplicates'] if r[1]=='V0002-2024-000182']
    table(c2/'_duplicates.qmd',['Supplier','Invoice date','Grand total'],[[r[0],r[2],money(r[3])] for r in repeated])
    departments=list(dict.fromkeys(r[0] for r in budgets)); amounts={(r[0],r[1]):r[2] for r in budgets}
    table(c2/'_budget-wide.qmd',['Department','January','February','March'],[[d]+[money(amounts[d,m]) for m in (1,2,3)] for d in departments])
    table(c2/'_budget-long.qmd',['Department','Month','Budget amount'],[[d,['January','February','March'][m-1],money(v)] for d,m,v in budgets if d==departments[0]])
    names=dict(keys['customers'])
    table(c3/'_keys.qmd',['SalesOrderID','CustomerID','Customer name'],[[o[0],o[2],names[o[2]]] for o in keys['orders']])
    table(c3/'_invoice-parts.qmd',['Invoice component','Amount'],[[label,money(v)] for label,v in zip(['SubTotal','FreightAmount','TaxAmount','GrandTotal'],parts)])
    table(c3/'_invoice-postings.qmd',['Account','Debit','Credit'],[[f'{r[0]} {r[1]}',money(r[2]) if r[2] else '—',money(r[3]) if r[3] else '—'] for r in trace['glr']])
    table(c3/'_shipment-postings.qmd',['Account','Debit','Credit'],[[f'{r[0]} {r[1]}',money(r[2]) if r[2] else '—',money(r[3]) if r[3] else '—'] for r in trace['gls']])
    figures={'chapter-02':{'freight-comparison':freight_svg(quality)},'chapter-03':{
        'customer-orders':pair('Customer and sales orders',RELATIONS['customer-orders'],markers['customer-orders'],(['PK  CustomerID','CustomerName'],['PK  SalesOrderID','FK  CustomerID'])),
        'order-lines':junction('Orders, items and order lines',[RELATIONS['order-lines'],RELATIONS['item-lines']],[markers['order-lines'],markers['item-lines']],['PK  SalesOrderLineID','FK  SalesOrderID','FK  ItemID']),
        'shipment-invoice':pair('Shipment and invoice lines',RELATIONS['shipment-invoice'],markers['shipment-invoice'],(['PK  ShipmentLineID'],['PK  SalesInvoiceLineID','FK  ShipmentLineID'])),
        'cash-applications':junction('Receipts applied to invoices',[RELATIONS['cash-applications'],RELATIONS['invoice-applications']],[markers['cash-applications'],markers['invoice-applications']],['PK  CashReceiptApplicationID','FK  CashReceiptID','FK  SalesInvoiceID']),
        'account-ledger':pair('Account and general ledger',RELATIONS['account-ledger'],markers['account-ledger'],(['PK  AccountID','AccountNumber'],['PK  GLEntryID','FK  AccountID'])),
        'work-order-close':pair('Work order and close',RELATIONS['work-order-close'],markers['work-order-close'],(['PK  WorkOrderID'],['PK  WorkOrderCloseID','FK  WorkOrderID'])),
        'crow-foot':notation()}}
    for chapter,images in figures.items():
        for name,doc in images.items():
            ET.fromstring(doc); path=folders[chapter]/(name+'.svg');path.write_text(doc,encoding='utf-8')
            subprocess.run([renderer,'--format','png','--width','2560','--output',str(path.with_suffix('.png')),str(path)],check=True)
    inv,sil,shl,shp,sol,so,cus,itm,app,rct=(trace[k] for k in ('inv','sil','shl','shp','sol','so','cus','itm','app','rct'))
    variables={'chapter-02':{'supplier_invoice':repeated[0][1],'budget_department':departments[0],
        'freight_mean':money(quality['freight_summary'][0]),'freight_largest':money(quality['freight_summary'][1])},
        'chapter-03':dict(invoice_id=inv[0],invoice_number=inv[1],invoice_date=inv[2],order_id=inv[3],
        customer_id=cus[0],customer_name=cus[1],invoice_total=money(inv[5]),line_id=sil[0],order_line_id=sil[1],
        shipment_line_id=shl[0],item_id=sil[3],quantity=f'{sil[4]:g}',unit_price=money(sil[5]),line_total=money(sil[6]),
        shipment_id=shl[1],shipment_number=shp[0],shipment_date=shp[1],order_number=so[0],order_date=so[1],
        item_code=itm[0],item_name=itm[1],standard_cost=money(itm[2]),extended_cost=money(shl[2]*itm[2]),
        application_id=app[0],receipt_id=app[1],applied_amount=money(app[2]),application_date=app[3],
        receipt_number=rct[0],receipt_amount=money(rct[1]),receipt_invoices=paid)}
    for chapter,folder in folders.items():
        data={'quality_examples':quality,'budgets':budgets} if chapter=='chapter-02' else {'key_example':keys,'sale_trace':trace,'relationship_markers':markers}
        facts={'schema_version':1,'dataset':pin,'generator_sha256':{n:_content_hash(root/n) for n in GENERATORS},
               'artifact_sha256':{n:_content_hash(folder/n) for n in ASSETS[chapter]},'variables':variables[chapter],**data}
        (folder/'facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Refreshed public Chapter 2–3 examples, native tables, and figures. Dataset checksum unchanged.')


if __name__=='__main__': refresh(ROOT)
