"""Prepare public Power BI teaching views without requiring Power BI in CI."""
from __future__ import annotations

from collections import Counter
import csv
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.calculations import bi_ch13 as essentials, bi_ch14 as dax
from shared.calculations import bi_ch15 as reports, bi_ch16 as monitoring
from shared.calculations.foundations import relationship
from scripts.slides.refresh import (_pin, _content_hash, sha256, _svg, _text, _rect, _line,
                                    BLUE, TEAL, GRAY, INK, RULE, WHITE)
from scripts.slides.refresh_foundations import table
from scripts.slides.refresh_excel import money, line_chart

GENERATORS = tuple(f'shared/calculations/bi_ch{n}.py' for n in range(13,17)) + (
    'shared/calculations/excel_analysis.py', 'shared/calculations/invoice_margin.py',
    'shared/calculations/foundations.py', 'scripts/slides/refresh_bi.py',
    'scripts/slides/refresh.py', 'scripts/slides/refresh_foundations.py',
    'scripts/slides/refresh_excel.py')
ASSETS = {
    'chapter-13': ('_profile.qmd','_validation.qmd','_selection.qmd','_discount-rate.qmd',
                   'filter-path.svg','filter-path.png'),
    'chapter-14': ('_merge.qmd','_margin.qmd','_filter-context.qmd','_income.qmd',
                   'star.svg','star.png'),
    'chapter-15': ('_gross-to-net.qmd','_budget-bridge.qmd','_classification.qmd',
                   '_window.qmd','window.svg','window.png','window.csv'),
    'chapter-16': ('_flags.qmd','_register.qmd','_rates.qmd','_review.qmd',
                   'monitoring.svg','monitoring.png'),
}


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
                errors.append(f'{chapter}: shared Power BI source changed; run --refresh-shared')
            if set(facts.get('artifact_sha256',{}))!=set(assets):
                errors.append(f'{chapter}: incomplete Power BI exhibit inventory')
            for name in assets:
                if not (folder/name).is_file() or facts['artifact_sha256'].get(name)!=_content_hash(folder/name):
                    errors.append(f'{chapter}: missing or modified generated artifact {name}')
        except (OSError,KeyError,TypeError,ValueError) as exc:
            errors.append(f'{chapter}: cannot validate public facts: {exc}')
    return errors


def model_node(name, x, y, fields):
    out=[_rect(x,y,420,160,WHITE,RULE,0),_rect(x,y,420,54,BLUE,BLUE,0),
         _text(x+16,y+38,name,32,WHITE,'bold')]
    out += [_text(x+16,y+94+i*44,field,31) for i,field in enumerate(fields)]
    return out


def arrow(x1,y1,x2,y2):
    return [f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{TEAL}" stroke-width="4" fill="none" marker-end="url(#filter-arrow)"/>']


ARROW = '<defs><marker id="filter-arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10" fill="'+TEAL+'"/></marker></defs>'


def refresh(root: Path) -> None:
    root=root.resolve();pin=_pin(root)
    path=(Path(os.environ.get('CHARLESRIVER_DATA',root/'datasets'))/'CharlesRiver.sqlite').resolve()
    before=sha256(path)
    if before!=pin['sha256']: raise ValueError('Pinned dataset checksum mismatch')
    renderer=os.environ.get('RSVG_CONVERT') or shutil.which('rsvg-convert')
    if not renderer: raise RuntimeError('rsvg-convert is required for explicit Power BI exhibit refresh')
    folders={n:root/f'shared/generated/chapter-{n}' for n in range(13,17)}
    for folder in folders.values(): folder.mkdir(parents=True,exist_ok=True)
    facts={n:{} for n in folders}
    def tbl(n,name,headers,rows): table(folders[n]/f'_{name}.qmd',headers,rows)
    def image(n,name,svg):
        out=folders[n]/f'{name}.svg';out.write_text(svg,encoding='utf-8')
        subprocess.run([renderer,'--format','png','--width','2560','--output',str(out.with_suffix('.png')),str(out)],check=True)
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON')
    try:
        all_lines=essentials.lines(db);year=[r for r in all_lines if r['fy']==2026]
        top,full=essentials._profile(db,1000),essentials._profile(db,None)
        revenue=sum(r['rev'] for r in year)
        facts[13].update(profile_top=top,profile_all=full,line_count=len(year),revenue=revenue)
        tbl(13,'profile',['Profile scope','Lines','Empty promotion IDs','Discount values'],[
            ['First 1,000',f"{top['n']:,}",f"{top['promo_empty']:,}",top['d_distinct']],
            ['Entire table',f"{full['n']:,}",f"{full['promo_empty']:,}",full['d_distinct']]])
        invoices=len({r['inv'] for r in year})
        tbl(13,'validation',['Fiscal 2026 control','Result'],[
            ['Invoice lines',f'{len(year):,}'],['Distinct invoices',f'{invoices:,}'],['Invoiced revenue',money(revenue)]])
        selected=[r for r in year if r['grp']=='Furniture']
        tbl(13,'selection',['Fiscal 2026 filter','Revenue','Invoices from lines'],[
            ['All item groups',money(revenue),f'{invoices:,}'],
            ['Furniture',money(sum(r['rev'] for r in selected)),f"{len({r['inv'] for r in selected}):,}"]])
        avg_rate=db.execute("SELECT AVG(l.Discount) FROM SalesInvoiceLine l JOIN SalesInvoice si USING(SalesInvoiceID) WHERE si.InvoiceDate BETWEEN '2026-01-01' AND '2026-12-31'").fetchone()[0]
        _,before_discount,_=reports.gross_to_net(db)
        weighted=sum(r['disc'] for r in year)/before_discount
        facts[13].update(invoice_count=invoices,mean_discount=avg_rate,weighted_discount=weighted)
        tbl(13,'discount-rate',['Fiscal 2026 calculation','Rate'],[
            ['Average of line Discount',f'{avg_rate:.2%}'],['Discount dollars / price before discount',f'{weighted:.2%}']])
        # These are the same key paths validated by the canonical Chapter 13 model.
        for edge in [('Customer','CustomerID','SalesInvoice','CustomerID'),
                     ('SalesInvoice','SalesInvoiceID','SalesInvoiceLine','SalesInvoiceID'),
                     ('Item','ItemID','SalesInvoiceLine','ItemID')]:
            assert relationship(db,*edge)[0]=='ERmandOne'
        out=[ARROW]+model_node('Customer',30,30,['CustomerID','CustomerSegment'])
        out+=model_node('SalesInvoice',830,30,['SalesInvoiceID','CustomerID'])
        out+=model_node('Item',30,310,['ItemID','ItemGroup'])
        out+=model_node('SalesInvoiceLine',830,310,['SalesInvoiceID','ItemID'])
        out+=arrow(456,110,816,110)+arrow(456,390,816,390)+arrow(1040,196,1040,296)
        for x,y,label in [(475,90,'1'),(782,90,'*'),(475,370,'1'),(782,370,'*'),(1064,223,'1'),(1064,283,'*')]:out.append(_text(x,y,label,34,INK,'bold'))
        out.append(_text(30,535,'Arrows show single-direction filters; the line table holds the amounts.',30,GRAY))
        image(13,'filter-path',_svg('The four-table sales model','Customer filters invoices, invoices filter lines, and Item filters lines. Each relationship is one to many.',out,height=570))

        merged=dax.lines(db);source_total=sum(r['rev'] for r in all_lines)
        assert len(merged)==len(all_lines) and abs(sum(r['rev'] for r in merged)-source_total)<.005
        tbl(14,'merge',['All invoice lines','Rows','Revenue'],[
            ['Before header merge',f'{len(all_lines):,}',money(source_total)],
            ['After header merge',f'{len(merged):,}',money(sum(r['rev'] for r in merged))]])
        margins=[dax.margin_pct(db,grp='Furniture',quarter=f'2026-Q{q}') for q in range(1,5)]
        tbl(14,'margin',['Furniture quarter','Margin at standard cost'],[[f'2026-Q{q}',f'{value:.2%}'] for q,value in enumerate(margins,1)])
        groups=['Furniture','Lighting','Textiles'];fixed=sum(r['rev'] for r in selected)
        tbl(14,'filter-context',['2026 row filter','Revenue','Furniture Revenue'],[
            [g,money(sum(r['rev'] for r in year if r['grp']==g)),money(fixed)] for g in groups])
        income={str(y):{kind:dax.pnl_total(db,y,kind) for kind in ('all','open')} for y in range(2024,2027)}
        tbl(14,'income',['Fiscal year','Including closing entries','Before closing entries'],[
            [y,money(round(values['all'],2)),money(values['open'])] for y,values in income.items()])
        facts[14].update(source_rows=len(all_lines),merged_rows=len(merged),source_revenue=source_total,
                         merged_revenue=sum(r['rev'] for r in merged),furniture_margin=margins,income=income)
        # Header fields in the shared line function validate the merged customer/date paths.
        customer_ids={r[0] for r in db.execute('SELECT CustomerID FROM Customer')}
        assert all(r['cust'] in customer_ids and dax.CALENDAR[0].isoformat()<=r['date']<=dax.CALENDAR[1].isoformat() for r in merged)
        out=[ARROW]+model_node('Customer',30,15,['CustomerID','CustomerSegment'])
        out+=model_node('Item',30,205,['ItemID','ItemGroup'])
        out+=model_node('Date',30,395,['Date','Year / YearMonth'])
        out += [_rect(830,150,420,300,WHITE,RULE,0),_rect(830,150,420,54,BLUE,BLUE,0),
                _text(846,188,'SalesInvoiceLine',32,WHITE,'bold')]
        out += [_text(846,254+i*70,field,31) for i,field in enumerate(['CustomerID','ItemID','InvoiceDate'])]
        for y,target in [(95,244),(285,314),(475,384)]:
            out+=arrow(456,y,816,target);out.append(_text(476,y-15,'1',32,INK,'bold'))
            label_y=y+(760-456)/(816-456)*(target-y)
            out.append(_text(760,label_y-15,'*',32,INK,'bold'))
        image(14,'star',_svg('The sales star after merging the invoice header','Customer, Item, and a complete Date table each filter SalesInvoiceLine directly. Every arrow is one to many and single direction.',out,height=585))

        listed,priced,net=reports.gross_to_net(db);budget=reports.budget_data(db)
        tbl(15,'gross-to-net',['Fiscal 2026 bridge','Amount'],[
            ['List amount',money(listed)],['Price changes before discount',money(priced-listed)],
            ['Discount to invoiced net',money(net-priced)],['Invoiced revenue',money(net)]])
        totals={key:sum(r[key] or 0 for r in budget['rows'].values()) for key in ('budget','actual','variance','volume','classification','remaining')}
        assert abs(totals['variance']-totals['volume']-totals['classification']-totals['remaining'])<.005
        tbl(15,'budget-bridge',['Operating-expense bridge','Actual less budget'],[
            ['Original variance',money(totals['variance'])],['Commission volume effect',money(totals['volume'])],
            ['Net classification effect',money(totals['classification'])],['Remaining variance',money(totals['remaining'])]])
        tbl(15,'classification',['Cost center','Depreciation classification effect'],[
            [name,money(budget['rows'][name]['classification'])] for name in ('Administration','Warehouse')])
        labels=[f'2026-{m:02}' for m in range(1,13)]
        baseline=[reports.ttm(db,m) for m in labels];visible=[reports.ttm(db,m,'2026-01') for m in labels]
        tbl(15,'window',['Month','Full model history','Axis begins Jan 2026'],[
            [labels[i],f'{baseline[i]:.2f}',f'{visible[i]:.2f}'] for i in (0,5,11)])
        image(15,'window',line_chart('Hours per standard hour: the window changes the result',
            [m if i in (0,5,11) else '' for i,m in enumerate(labels)],
            [('Model history',baseline,BLUE,False),('Filtered visual axis',visible,TEAL,True)],
            unit='Labor hours / standard hour',top=2,ticks=[0,.5,1,1.5,2],
            note='Both use ratios of summed hours. The visible axis contains only 2026.'))
        with (folders[15]/'window.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream);writer.writerow(['month','model_history','visible_2026_axis']);writer.writerows(zip(labels,baseline,visible))
        facts[15].update(gross_to_net=[listed,priced,net],budget_totals=totals,budget=budget,
                         window={'months':labels,'model_history':baseline,'visible_axis':visible})

        journals=monitoring.journal_entries(db);register=monitoring.register(db);pops=monitoring.populations(db)
        counts=Counter(r['test'] for r in register);reviewed=monitoring.reviewed_register(db)
        tbl(16,'flags',['Journal-entry rule','Flagged entries'],[[flag,sum(r['flags'][flag] for r in journals)] for flag in monitoring.JE_FLAGS])
        tbl(16,'register',['Process','Test failures','Distinct documents'],[
            [name,sum(1 for r in register if r['test'].startswith(prefix)),len({r['doc'] for r in register if r['test'].startswith(prefix)})]
            for prefix,name in monitoring.PROCESS.items()])
        rate_rows=[]
        for key in ('JE SelfApproved','PO SelfApproved','PR SelfApproved'):
            denominator=pops[monitoring.PROCESS[key[:2]]];rate=1000*counts[key]/denominator
            rate_rows.append([key.removesuffix(' SelfApproved'),counts[key],f'{denominator:,}',f'{rate:.2f}'])
        tbl(16,'rates',['Self-approval process','Failures','Population','Per 1,000'],rate_rows)
        dispositions=Counter(r['disposition'] or 'Open' for r in reviewed)
        tbl(16,'review',['Tutorial 16.3 disposition','Exceptions'],[[k,dispositions[k]] for k in ('Expected','Deficiency','Follow up','Open')])
        assert sum(dispositions.values())==len(register)
        facts[16].update(populations=pops,counts=dict(counts),exceptions=len(register),
                         distinct_documents=len({r['doc'] for r in register}),dispositions=dict(dispositions))
        out=[ARROW]
        for x,y,name,detail in [(30,35,'Rule','Population and threshold'),(830,35,'Population','Completeness and coverage'),
                                (830,320,'Exceptions','Document + test'),(30,320,'Disposition','Evidence and follow-up')]:
            out+=model_node(name,x,y,[detail])
        out+=arrow(456,115,816,115)+arrow(1040,201,1040,306)+arrow(824,400,464,400)+arrow(240,314,240,209)
        image(16,'monitoring',_svg('A repeatable monitoring cycle','Define the rule, validate the population, retain failed document-test pairs, review evidence, and revise the rule or control.',out,height=520))
    finally: db.close()
    if sha256(path)!=before: raise RuntimeError('Dataset changed during read-only Power BI refresh')
    for n,folder in folders.items():
        data={'schema_version':1,'dataset':pin,'generator_sha256':{name:_content_hash(root/name) for name in GENERATORS},
              'artifact_sha256':{name:_content_hash(folder/name) for name in ASSETS[f'chapter-{n}']},'public_examples':facts[n]}
        (folder/'facts.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Refreshed public Chapters 13-16 Power BI exhibits; dataset checksum unchanged.')


if __name__=='__main__': refresh(ROOT)
