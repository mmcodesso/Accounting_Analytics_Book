"""Supplemental Chapter 2 public evidence; only explicit refresh opens the dataset.

Keep the existing Chapter 1 and foundations generators independent. Canonical
Draw.io sources supply the field/link vocabulary; read-only queries verify the
selected records. Ordinary builds check the committed facts without datasets.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import html
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
from scripts.slides.refresh import (_content_hash, _pin, sha256, _svg, _text,
                                    _rect, _line, BLUE, TEAL, INK, GRAY, RULE, WHITE)

OUTPUT = Path('shared/generated/chapter-02/storytelling')
GENERATORS = ('scripts/slides/refresh_chapter02_storytelling.py', 'scripts/slides/refresh.py')
INPUTS = ('shared/generated/chapter-02/facts.json',
          'visuals/src/fig-02-05-salesinvoice-date-check.drawio',
          'visuals/src/fig-02-07-glentry-debit-credit-sum.drawio',
          'visuals/src/fig-01-06-ledger-posting-trace.drawio')
FRAGMENTS = ('_invoice-date-task.qmd', '_invoice-date-response.qmd', '_ledger-totals.qmd',
             '_account-task.qmd', '_account-response.qmd', '_period-coverage.qmd',
             '_amount-task.qmd', '_amount-response.qmd', '_budget-wide.qmd', '_budget-long.qmd')
ASSETS = FRAGMENTS + ('posting-trace.svg', 'posting-trace.png')


def content_hash(path: Path) -> str:
    if path.suffix.lower() in {'.json', '.drawio'}:
        return hashlib.sha256(path.read_text(encoding='utf-8-sig').encode('utf-8')).hexdigest()
    return _content_hash(path)


def hashes(root: Path, names: tuple) -> dict:
    return {name: content_hash(root / name) for name in names}


def check_fresh(root: Path, manifest: dict) -> list[str]:
    if (OUTPUT / 'facts.json').as_posix() not in manifest.get('public_assets', []):
        return []
    errors = []
    try:
        facts = json.loads((root / OUTPUT / 'facts.json').read_text(encoding='utf-8'))
        if facts.get('schema_version') != 1 or facts.get('dataset') != _pin(root):
            errors.append('chapter-02 storytelling: dataset pin changed; run focused --refresh-shared')
        for key, names in [('generator_sha256', GENERATORS), ('input_sha256', INPUTS)]:
            if facts.get(key) != hashes(root, names):
                errors.append(f'chapter-02 storytelling: {key} changed; run focused --refresh-shared')
        if set(facts.get('artifact_sha256', {})) != set(ASSETS):
            errors.append('chapter-02 storytelling: incomplete artifact inventory')
        for name in ASSETS:
            path = root / OUTPUT / name
            if not path.is_file() or facts.get('artifact_sha256', {}).get(name) != content_hash(path):
                errors.append(f'chapter-02 storytelling: missing or modified {name}')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'chapter-02 storytelling: cannot validate public inputs: {exc}')
    return errors


def table(path: Path, headers: list, rows: list) -> None:
    def line(row):
        return '| ' + ' | '.join(str(v).replace('|', '\\|') for v in row) + ' |\n'
    path.write_text(line(headers) + line(['---'] * len(headers)) + ''.join(map(line, rows)), encoding='utf-8')


def examples(db: sqlite3.Connection) -> dict:
    """Selected public tutorial records, not answers to assigned exercises."""
    invoice = db.execute('SELECT s.SalesInvoiceID,s.InvoiceNumber,s.InvoiceDate,s.SalesOrderID,'
        'MIN(sh.ShipmentDate) FROM SalesInvoice s JOIN Shipment sh USING(SalesOrderID) '
        'WHERE s.InvoiceNumber=? GROUP BY s.SalesInvoiceID', ('SI-2024-000001',)).fetchone()
    totals = db.execute('SELECT ROUND(SUM(Debit),2),ROUND(SUM(Credit),2),'
        'ROUND(SUM(Debit)-SUM(Credit),2) FROM GLEntry').fetchone()
    coverage = db.execute('SELECT MIN(PostingDate),MAX(PostingDate),MAX(FiscalYear) FROM GLEntry').fetchone()
    tail = db.execute('SELECT SourceDocumentType,COUNT(*) FROM GLEntry WHERE FiscalYear=? '
                      'GROUP BY SourceDocumentType', (coverage[2],)).fetchall()
    trace = db.execute('SELECT g.GLEntryID,g.PostingDate,g.AccountID,g.Debit,g.Credit,'
        'g.SourceDocumentType,g.SourceDocumentID,g.SourceLineID,s.InvoiceNumber,s.GrandTotal,'
        'l.Quantity,l.UnitPrice,a.AccountNumber,a.AccountName,a.ParentAccountID '
        'FROM GLEntry g JOIN SalesInvoice s ON s.SalesInvoiceID=g.SourceDocumentID '
        'JOIN SalesInvoiceLine l ON l.SalesInvoiceLineID=g.SourceLineID '
        'JOIN Account a ON a.AccountID=g.AccountID WHERE g.GLEntryID=?', (126312,)).fetchone()
    if list(invoice or ()) != [1,'SI-2024-000001','2024-01-01',41,'2024-01-03']:
        raise ValueError('Approved invoice-date example changed; editorial review required')
    if not trace or list(trace[:3]) != [126312,'2025-03-05',42] or list(trace[6:8]) != [7947,10645]:
        raise ValueError('Approved posting identifiers changed; editorial review required')
    if (round(trace[4],2), round(trace[9],2), trace[10], round(trace[11],2), trace[12]) != (688.42,787.48,2,344.21,4010):
        raise ValueError('Approved posting amounts changed; editorial review required')
    if abs(trace[10] * trace[11] - trace[4]) > .005:
        raise ValueError('Invoice line no longer agrees with the selected credit')
    return {'invoice_date': invoice, 'whole_extract_totals': totals, 'coverage': coverage,
            'latest_year_sources': tail, 'trace': trace}


def trace_view(trace: list) -> str:
    # Use the canonical source-document and source-line field meanings, with a
    # presentation geometry that leaves each key readable at teaching size.
    out = [_text(32,45,'5 March 2025 · one revenue posting',34,BLUE,'bold')]
    panels = [('SalesInvoice', ['SalesInvoiceID  '+str(trace[6])]),
              ('SalesInvoiceLine', ['SalesInvoiceLineID  '+str(trace[7]), 'SalesInvoiceID  '+str(trace[6])]),
              ('GLEntry', ['GLEntryID  '+str(trace[0]), 'SourceDocumentID  '+str(trace[6]),
                           'SourceLineID  '+str(trace[7])])]
    for i,(label,fields) in enumerate(panels):
        x = 20+i*430
        out.extend([_rect(x,90,400,260,WHITE,RULE,0),_rect(x,90,400,61,BLUE,BLUE,0),
                    _text(x+18,132,label,32,WHITE,'bold')])
        out.extend(_text(x+18,199+j*53,field,29) for j,field in enumerate(fields))
        if i<2:
            out.append(_line(x+400,220,x+430,220,TEAL))
    out.extend([_text(640,410,'Source → ledger: look for expected postings',32,TEAL,'bold','middle'),
                _text(640,463,'Ledger → source: locate support for recorded postings',32,INK,'normal','middle')])
    return _svg('One invoice-line posting: trace direction',
        'Focused adaptation of Figure 1.6. SalesInvoice 7947 contains SalesInvoiceLine 10645. '
        'GLEntry 126312 identifies that document and line. The first direction tests for expected '
        'postings; the reverse locates support. A single match cannot establish population completeness.',
        out,height=495)


def refresh(root: Path) -> None:
    root = root.resolve()
    pin = _pin(root)
    database = (Path(os.environ.get('CHARLESRIVER_DATA',root/'datasets'))/'CharlesRiver.sqlite').resolve()
    before = sha256(database)
    if before != pin['sha256']:
        raise ValueError('Pinned dataset checksum mismatch')
    renderer = os.environ.get('RSVG_CONVERT') or shutil.which('rsvg-convert')
    if not renderer:
        raise RuntimeError('rsvg-convert is required for explicit shared refresh')
    # Parse authorities rather than relying on a separately maintained diagram.
    vocabulary = ' '.join(html.unescape(c.get('value','')) for rel in INPUTS[1:]
                           for c in ET.parse(root/rel).iter('mxCell'))
    for required in ('InvoiceDate','SalesOrderID','Debit','Credit','SourceDocumentID','SourceLineID'):
        if required not in vocabulary:
            raise ValueError(f'Canonical diagram field changed: {required}')
    db = sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        data = examples(db)
    finally:
        db.close()
    if sha256(database) != before:
        raise RuntimeError('Dataset changed during read-only refresh')
    folder = root/OUTPUT
    folder.mkdir(parents=True,exist_ok=True)
    money = lambda value: f'${value:,.2f}'
    inv, trace = data['invoice_date'], data['trace']
    short_date = lambda text: date.fromisoformat(text).strftime('%d %b %Y')
    table(folder/'_invoice-date-task.qmd',['Invoice','Order ID','Invoice date','Earliest shipment'],
          [[inv[1],inv[3],short_date(inv[2]),short_date(inv[4])]])
    table(folder/'_invoice-date-response.qmd',['Invoice','Invoice date','Earliest shipment','Flag'],
          [[inv[1],short_date(inv[2]),short_date(inv[4]),'**Check**']])
    table(folder/'_ledger-totals.qmd',['Whole-extract measure','Amount'],
          [[label,money(v)] for label,v in zip(('Total debits','Total credits','Difference'),data['whole_extract_totals'])])
    table(folder/'_account-task.qmd',['Record','Field','Value'],
          [['GLEntry '+str(trace[0]),'AccountID',trace[2]],['Account row','AccountID',trace[2]],
           ['Account row','AccountNumber',trace[12]]])
    table(folder/'_account-response.qmd',['AccountID','AccountNumber','AccountName'],
          [[trace[2],trace[12],trace[13]]])
    table(folder/'_period-coverage.qmd',['Population boundary','Observed coverage'],
          [['Review period','Fiscal 2024–2026'],['Ledger posting dates',short_date(data['coverage'][0])+' to '+short_date(data['coverage'][1])],
           ['Fiscal '+str(data['coverage'][2])+' tail','; '.join(str(count)+' '+kind+' postings' for kind,count in data['latest_year_sources'])]])
    table(folder/'_amount-task.qmd',['Evidence','Amount'],
          [['GLEntry '+str(trace[0])+' revenue credit',money(trace[4])],
           ['Invoice line '+str(trace[7]),money(trace[10]*trace[11])],
           ['Invoice '+str(trace[6])+' grand total',money(trace[9])]])
    (folder/'_amount-response.qmd').write_text(
        f'**{trace[10]:g} × {money(trace[11])} = {money(trace[4])}**\n\n'
        f'Invoice line **{trace[7]}** agrees with revenue credit **{trace[0]}**.\n\n'
        f'The invoice grand total of **{money(trace[9])}** has a different scope.\n',encoding='utf-8')
    base = json.loads((root/INPUTS[0]).read_text(encoding='utf-8'))
    budgets = base['budgets']
    departments = list(dict.fromkeys(r[0] for r in budgets))
    amounts = {(r[0],r[1]):r[2] for r in budgets}
    table(folder/'_budget-wide.qmd',['Department','January','February','March'],
          [[('**'+d+'**') if d=='Sales' else d]+[('**'+money(amounts[d,m])+'**') if d=='Sales' else money(amounts[d,m]) for m in (1,2,3)] for d in departments])
    table(folder/'_budget-long.qmd',['Department','Month','Budget amount'],
          [['**'+d+'**',['January','February','March'][m-1],'**'+money(v)+'**'] for d,m,v in budgets if d=='Sales'])
    svg = folder/'posting-trace.svg'
    svg.write_text(trace_view(trace),encoding='utf-8')
    subprocess.run([renderer,'--width','2560','--output',str(folder/'posting-trace.png'),str(svg)],check=True)
    facts = {'schema_version':1,'dataset':pin,'generator_sha256':hashes(root,GENERATORS),
             'input_sha256':hashes(root,INPUTS),'artifact_sha256':hashes(folder,ASSETS),
             **data,'budget_example':budgets,'review_period':[2024,2026],
             'text_hash_policy':'UTF-8 normalized LF; dataset and PNG use raw bytes'}
    (folder/'facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Refreshed Chapter 2 storytelling evidence; dataset SHA-256 unchanged ({before}).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    if args.check:
        errors = check_fresh(ROOT,{'public_assets':[(OUTPUT/'facts.json').as_posix()]})
        for error in errors: print(error,file=sys.stderr)
        raise SystemExit(bool(errors))
    refresh(ROOT)
