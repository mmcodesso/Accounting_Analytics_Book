"""Refresh public SQL teaching exhibits from the book's shared tutorial queries."""
from __future__ import annotations

import csv
import importlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.slides.refresh import _pin, _content_hash, sha256, BLUE, TEAL, GRAY
from scripts.slides.refresh_foundations import table, pair
from scripts.slides.refresh_excel import money, line_chart
from shared.calculations.foundations import relationship

GENERATORS = tuple(f'shared/calculations/sql_ch{n:02}.py' for n in range(9,13)) + (
    'scripts/slides/refresh_sql.py', 'scripts/slides/refresh.py',
    'scripts/slides/refresh_foundations.py', 'scripts/slides/refresh_excel.py',
    'shared/calculations/foundations.py')

# Each slice preserves the tokens of a public tutorial query. The surrounding
# teaching slide identifies excerpts; the book retains the complete script.
SNIPPETS = {
    9: {'account_columns':(0,None), 'variance_check':(0,None),
        'accounts_by_number':(0,None), 'source_types':(0,None),
        'check_failures':(0,None), 'open_work_orders':(0,None),
        'top_ten-columns':('top_ten',0,8), 'top_ten-order':('top_ten',8,None),
        'review_threshold':(0,None)},
    10: {'closes_to_work_orders':(0,None), 'variance_by_group':(0,None),
         'ledger_variance':(0,None)},
    11: {'payroll_categories':(1,9), 'end_of_records':(0,None),
         'hours_by_month':(0,5), 'query_view':(0,None)},
    12: {'trace':(0,8), 'unbilled_shipments':(0,6),
         'approval_summary':(0,6)},
}
TABLES = {
    9: ('accounts','checks','largest'),
    10: ('groups','ledger','output','hours','parts'),
    11: ('categories','payroll','early-months','ranked-gap','view'),
    12: ('journal-control','payroll-control','trace','match','price','grni',
         'approvals','time-profile','pay-expectation','surge','late'),
}
ASSETS = {f'chapter-{n:02}':tuple(
    [f'_{name}.qmd' for name in TABLES[n]] +
    [f'_query-{name}.qmd' for name in SNIPPETS[n]] +
    (['item-workorder.svg','item-workorder.png'] if n==10 else []) +
    (['trailing.svg','trailing.png','trailing.csv'] if n==11 else []))
    for n in range(9,13)}


def check_fresh(root: Path, manifest: dict) -> list[str]:
    errors=[]
    for chapter,assets in ASSETS.items():
        rel=f'shared/generated/{chapter}/facts.json'
        if rel not in manifest.get('public_assets',[]): continue
        try:
            folder=root/'shared/generated'/chapter
            facts=json.loads((root/rel).read_text(encoding='utf-8'))
            if facts.get('schema_version')!=1 or facts.get('dataset')!=_pin(root):
                errors.append(f'{chapter}: dataset pin changed; run --refresh-shared')
            if facts.get('generator_sha256')!={n:_content_hash(root/n) for n in GENERATORS}:
                errors.append(f'{chapter}: shared SQL or figure source changed; run --refresh-shared')
            if set(facts.get('artifact_sha256',{}))!=set(assets):
                errors.append(f'{chapter}: incomplete public SQL exhibit inventory')
            for name in assets:
                if not (folder/name).is_file() or facts['artifact_sha256'].get(name)!=_content_hash(folder/name):
                    errors.append(f'{chapter}: missing or modified generated artifact {name}')
        except (OSError,KeyError,TypeError,ValueError) as exc:
            errors.append(f'{chapter}: cannot validate public facts: {exc}')
    return errors


def query_result(db: sqlite3.Connection, chapter: int, key: str) -> dict:
    """Run a public SELECT against the caller's connection; never create a view."""
    module=importlib.import_module(f'shared.calculations.sql_ch{chapter:02}')
    sql=next(sql for name,_,sql in module.QUERIES if name==key)
    if key=='query_view':
        sql=f'WITH MonthlyLaborEfficiency AS ({module._CHAIN}{module._FINAL})\n'+sql
    if not sql.startswith(('SELECT','WITH')):
        raise ValueError('Only public read queries may generate slide facts')
    cur=db.execute(sql)
    return {'columns':[col[0] for col in cur.description], 'rows':cur.fetchall()}


def refresh(root: Path) -> None:
    root=root.resolve();pin=_pin(root)
    path=(Path(os.environ.get('CHARLESRIVER_DATA',root/'datasets'))/'CharlesRiver.sqlite').resolve()
    before=sha256(path)
    if before!=pin['sha256']: raise ValueError('Pinned dataset checksum mismatch')
    renderer=os.environ.get('RSVG_CONVERT') or shutil.which('rsvg-convert')
    if not renderer: raise RuntimeError('rsvg-convert is required for explicit SQL exhibit refresh')
    results={n:{} for n in range(9,13)}
    folders={n:root/f'shared/generated/chapter-{n:02}' for n in results}
    for folder in folders.values(): folder.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    db.execute('PRAGMA query_only=ON')
    def get(n,key):
        if key not in results[n]: results[n][key]=query_result(db,n,key)
        return results[n][key]['rows']
    def tbl(n,name,headers,rows): table(folders[n]/f'_{name}.qmd',headers,rows)
    def image(n,name,svg):
        out=folders[n]/f'{name}.svg';out.write_text(svg,encoding='utf-8')
        subprocess.run([renderer,'--format','png','--width','2560','--output',str(out.with_suffix('.png')),str(out)],check=True)
    try:
        for n,specs in SNIPPETS.items():
            module=importlib.import_module(f'shared.calculations.sql_ch{n:02}')
            queries={key:sql for key,_,sql in module.QUERIES}
            for name,spec in specs.items():
                key,start,end=spec if len(spec)==3 else (name,*spec)
                code='\n'.join(queries[key].splitlines()[start:end])
                if n == 11 and name == 'payroll_categories':
                    # Remove the outer SELECT indentation and use compact nesting
                    # so the public CASE excerpt fits both presentation formats.
                    code=textwrap.dedent(code)
                    code='\n'.join(' ' * ((len(line)-len(line.lstrip()))//2)+line.lstrip()
                                   for line in code.splitlines())
                    code=code.replace(", 'Overtime Earnings'", ",\n      'Overtime Earnings'")
                    code=code.replace(", 'Employer Benefits'", ",\n      'Employer Benefits'")
                (folders[n]/f'_query-{name}.qmd').write_text('```sql\n'+code+'\n```\n',encoding='utf-8')
        tbl(9,'accounts',['AccountID','Account number','Name'],get(9,'accounts_by_number'))
        checks=get(9,'variance_check')
        tbl(9,'checks',['Close ID','Material','Conversion','Total','Check'],[
            [r[0],*[money(v) for v in r[2:]]] for r in checks[:3]])
        # Keep only the displayed sample and its independently tested population.
        results[9]['variance_check']['population_count']=len(checks)
        results[9]['variance_check']['rows']=checks[:3]
        failures=get(9,'check_failures')
        if failures: raise ValueError('Public variance component reconciliation changed')
        tbl(9,'largest',['Close ID','Labor','Overhead','Total'],[
            [r[0],money(r[4]),money(r[5]),money(r[6])] for r in get(9,'top_ten')[:3]])
        groups=get(10,'variance_by_group');ledger=get(10,'ledger_variance')[0][0]
        if abs(sum(r[2] for r in groups)-ledger)>.005: raise ValueError('Work-order closes no longer reconcile')
        tbl(10,'groups',['Item group','Closes','Variance'],[[r[0],f'{r[1]:,}',money(r[2])] for r in groups])
        tbl(10,'ledger',['Fiscal 2026 check','Variance'],[['Sum of item groups',money(sum(r[2] for r in groups))],['Account 5080 close postings',money(ledger)]])
        tbl(10,'output',['Completion year','Units','Standard hours'],[[r[0],f'{r[1]:,.0f}',f'{r[2]:,.0f}'] for r in get(10,'output')])
        hours=get(10,'hours_by_type')
        tbl(10,'hours',['Work year','Labor type','Hours / standard hour'],[[r[0],r[1].replace(' Manufacturing',''),f'{r[4]:.2f}'] for r in hours])
        tbl(10,'parts',['Close year','Direct labor variance','Overhead variance'],[[r[0],money(r[1]),money(r[2])] for r in get(10,'variance_parts')])
        rel=('Item','ItemID','WorkOrder','ItemID')
        image(10,'item-workorder',pair('The item key supplies the product group',rel,relationship(db,*rel),
             (['PK  ItemID','ItemGroup'],['PK  WorkOrderID','FK  ItemID'])))
        categories=get(11,'payroll_categories');charged=get(11,'payroll_ledger')[0][0]
        components=sum(r[1] for r in categories if r[0]!='Employee deductions')
        if abs(components-charged)>.005: raise ValueError('Classified payroll no longer reconciles')
        tbl(11,'categories',['Category','Fiscal 2026 amount'],[[r[0],money(r[1])] for r in categories])
        tbl(11,'payroll',['Manufacturing cost check','Amount'],[['Pay + employer costs',money(components)],['Account 1090 payroll debits',money(charged)]])
        tbl(11,'early-months',['Work month','Days','Direct hours','Indirect hours'],[[r[0],r[1],f'{r[2]:,.0f}',f'{r[3]:,.0f}'] for r in get(11,'hours_by_month')[:6]])
        tbl(11,'ranked-gap',['Year','Month','Gap','Pay dates'],[[r[0],r[1],money(r[2]),r[3]] for r in get(11,'gap_pay_dates') if r[4]==1])
        trailing=get(11,'measure_trailing');view=get(11,'query_view')
        assert view==[r for r in trailing if r[0]>='2026-01']
        assert get(11,'measure_monthly')==[(36,)]
        tbl(11,'view',['Month','TTM direct','TTM indirect','TTM total'],[[r[0],*[f'{v:.2f}' for v in r[2:5]]] for r in view[-3:]])
        labels=[r[0] if i in (0,6,12,18,24) else '' for i,r in enumerate(trailing)]
        image(11,'trailing',line_chart('Labor hours per standard hour: trailing twelve months',labels,
            [('Direct',[r[2] for r in trailing],BLUE,False),('Indirect',[r[3] for r in trailing],TEAL,'3 7'),
             ('Total',[r[4] for r in trailing],GRAY,True)],unit='Hours / standard hour',top=2,ticks=[0,.5,1,1.5,2],
            note='Ratios of summed hours. The output window ends with the time-record coverage.'))
        with (folders[11]/'trailing.csv').open('w',encoding='utf-8',newline='') as out:
            writer=csv.writer(out);writer.writerow(results[11]['measure_trailing']['columns']);writer.writerows(trailing)
        je=get(12,'je_population')[0]
        tbl(12,'journal-control',['Population','Entries','Amount'],[['JournalEntry',f'{je[0]:,}',money(je[1])],['Related ledger debits',f'{je[2]:,}',money(je[3])]])
        tbl(12,'payroll-control',['Fiscal year','Register cost','Ledger cost','Difference'],[[r[0],*[money(v) for v in r[1:]]] for r in get(12,'payroll_population')])
        trace=get(12,'trace')
        tbl(12,'trace',['Posting ID','Date','Debit + credit'],[[r[1],r[2],money(r[3])] for r in trace])
        tbl(12,'match',['Purchase-order-line status','Lines'],[[r[0],f'{r[1]:,}'] for r in get(12,'match_status')])
        price=get(12,'price_tolerance')[0]
        tbl(12,'price',['Price test','Invoice lines'],[['Population',f'{price[0]:,}'],['Above 3% difference',f'{price[1]:,}'],['Above 2% difference',f'{price[2]:,}']])
        grni=get(12,'grni')[0]
        tbl(12,'grni',['Unbilled-receipt control','Amount'],[['Receipt value not invoiced',money(grni[0])],['Account 2020 balance',money(grni[1])],['Difference',money(grni[0]-grni[1])]])
        tbl(12,'approvals',['Approval test','Orders','Order value'],[[r[0],r[1],money(r[2])] for r in get(12,'approval_summary')])
        profile=get(12,'time_profile')[0]
        tbl(12,'time-profile',['Time-clock profile','Result'],[['Entries',f'{profile[0]:,}'],['Not approved',profile[1]],['No clock-out',profile[2]],['Last work date',profile[5]]])
        tbl(12,'pay-expectation',['Year','Aggregate difference','Lines above one cent'],[[r[0],money(r[3]),r[4]] for r in get(12,'pay_expectation')])
        tbl(12,'surge',['Work year','Surge days','Employees per day','Share of overtime'],[[r[0],r[1],r[2],f'{r[4]:.1%}'] for r in get(12,'surge_days')])
        tbl(12,'late',['Work year','Direct hours after end','Share of direct hours'],[[r[0],f'{r[2]:,.0f}',f'{r[3]:.1%}'] for r in get(12,'late_by_year')])
    finally: db.close()
    if sha256(path)!=before: raise RuntimeError('Dataset changed during read-only refresh')
    for n,folder in folders.items():
        facts={'schema_version':1,'dataset':pin,'generator_sha256':{name:_content_hash(root/name) for name in GENERATORS},
               'artifact_sha256':{name:_content_hash(folder/name) for name in ASSETS[f'chapter-{n:02}']},'queries':results[n]}
        if n==9: facts['variables']={'closes':f'{len(checks):,}','failed_checks':len(failures)}
        (folder/'facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Refreshed public Chapters 9-12 SQL exhibits; dataset checksum unchanged.')


if __name__=='__main__': refresh(ROOT)
