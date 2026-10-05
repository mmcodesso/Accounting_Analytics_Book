"""Public, dataset-free slide exhibits for the Excel teaching phase."""
from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.calculations import excel_analysis as calc
from shared.calculations.foundations import sale_trace
from shared.calculations.invoice_margin import invoice_lines
from scripts.slides.refresh import (_pin, _content_hash, sha256, _svg, _text, _rect,
                                    _line, BLUE, TEAL, GRAY, INK, TINT, WHITE, RULE)
from scripts.slides.refresh_foundations import table

FIGURE = 'fig-04-05-cell-reference-types'
GENERATORS = ('shared/calculations/excel_analysis.py', 'shared/calculations/invoice_margin.py',
              'shared/calculations/foundations.py', 'scripts/slides/refresh_excel.py',
              'scripts/slides/refresh.py', 'scripts/slides/refresh_foundations.py',
              'scripts/figures/ch04.py', f'visuals/src/{FIGURE}.drawio', f'visuals/svg/{FIGURE}.svg')
ASSETS = {
    'chapter-04': ('relative.svg','relative.png','absolute.svg','absolute.png','mixed.svg','mixed.png','_control-totals.qmd'),
    'chapter-05': ('lookup.svg','lookup.png','_merge-check.qmd'),
    'chapter-06': ('histogram.svg','histogram.png','histogram.csv','bridge.svg','bridge.png',
                   '_profile.qmd','_bridge.qmd','_driver-totals.qmd','_margin-rates.qmd'),
    'chapter-07': ('monthly.svg','monthly.png','monthly.csv','_regressions.qmd','_backtest.qmd',
                   '_budget.qmd','_scenarios.qmd'),
    'chapter-08': ('benford.svg','benford.png','benford.csv','_payment-control.qmd',
                   '_benford.qmd','_aging.qmd','_ar-reconcile.qmd','_scores.qmd'),
}


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


def money(value): return f'(${abs(value):,.2f})' if value < 0 else f'${value:,.2f}'
def percent(value): return f'{value:.2%}'


def line_chart(title, labels, series, *, unit, top, ticks, note=''):
    """Shared presentation profile, with labels and line patterns as well as color."""
    left, right, bottom, height = 130, 1210, 450, 325
    out = [_text(30,45,title,34,BLUE,'bold')]
    for value in ticks:
        y = bottom - height*value/top
        out += [_line(left,y,right,y,RULE), _text(left-18,y+10,f'{value:g}',29,GRAY,anchor='end')]
    out.append(_text(20,92,unit,28,GRAY))
    for i,label in enumerate(labels):
        x=left+(right-left)*i/(len(labels)-1)
        if label: out.append(_text(x,bottom+42,label,29,GRAY,anchor='middle'))
    for j,(label,values,color,dashed) in enumerate(series):
        coords=[(left+(right-left)*i/(len(values)-1),bottom-height*v/top) for i,v in enumerate(values)]
        points=' '.join(f'{x:.2f},{y:.2f}' for x,y in coords)
        pattern='12 8' if dashed is True else dashed
        dash=f' stroke-dasharray="{pattern}"' if pattern else ''
        out.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="4"{dash}/>')
        x=30+j*410
        out.append(f'<path d="M{x} 548h65" stroke="{color}" stroke-width="4"{dash}/>')
        out.append(_text(x+78,558,label,29,INK))
    if note: out.append(_text(30,620,note,28,GRAY))
    return _svg(title,title+'. '+note,out,height=650)


def refresh(root: Path) -> None:
    root=root.resolve();pin=_pin(root)
    database=(Path(os.environ.get('CHARLESRIVER_DATA',root/'datasets'))/'CharlesRiver.sqlite').resolve()
    before=sha256(database)
    if before!=pin['sha256']: raise ValueError('Pinned dataset checksum mismatch')
    renderer=os.environ.get('RSVG_CONVERT') or shutil.which('rsvg-convert')
    if not renderer: raise RuntimeError('rsvg-convert is required for explicit shared refresh')
    db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    try:
        lines=invoice_lines(db);trace=sale_trace(db)
        source_count,source_total=db.execute('SELECT COUNT(*),SUM(LineTotal) FROM SalesInvoiceLine').fetchone()
        invoice_total=db.execute('SELECT SUM(SubTotal) FROM SalesInvoice').fetchone()[0]
        bridge=calc.margin_bridge(db);months=calc.monthly_revenue(db)
        budget=calc.flex(db);model=calc.promotion_model(db);backtest=calc.forecast_backtest(db)
        payments=calc.payments(db);aging=calc.aging(db);journals=calc.journal_entries(db)
    finally: db.close()
    if sha256(database)!=before: raise RuntimeError('Dataset changed during read-only refresh')
    if len(lines)!=source_count or abs(sum(r['R'] for r in lines)-source_total)>.005:
        raise ValueError('Merged invoice-line population changed')
    folders={c:root/'shared/generated'/c for c in ASSETS}
    for folder in folders.values(): folder.mkdir(parents=True,exist_ok=True)
    def tbl(ch,name,headers,rows): table(folders[f'chapter-{ch:02d}']/(name+'.qmd'),headers,rows)
    def csv_out(ch,name,headers,rows):
        with (folders[f'chapter-{ch:02d}']/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(headers);w.writerows(rows)
    images={c:{} for c in ASSETS}
    # Crop complete book panels. No internal text or evidence is redrawn.
    original=(root/f'visuals/svg/{FIGURE}.svg').read_text(encoding='utf-8')
    for name,x in [('relative',0),('absolute',294),('mixed',588)]:
        svg=ET.fromstring(original)
        # Percentage foreignObject bounds otherwise shrink to the cropped
        # viewport in Chrome and clip labels in the second and third panels.
        for label in svg.iter('{http://www.w3.org/2000/svg}foreignObject'):
            label.set('width',svg.get('width','863').removesuffix('px'))
            label.set('height',svg.get('height','263').removesuffix('px'))
        svg.set('viewBox',f'{x} 0 274 230');svg.set('width','548');svg.set('height','460')
        images['chapter-04'][name]=ET.tostring(svg,encoding='unicode')
    tbl(4,'_control-totals',['Control','Amount'],[
        ['Invoice lines',money(source_total)],['Invoice subtotals',money(invoice_total)],
        ['Difference, rounded to cents',money(round(source_total-invoice_total,2))]])
    inv,sil=trace['inv'],trace['sil']
    out=[_text(30,48,'Lookup value, matching key, return value',34,BLUE,'bold')]
    for x,title,rows in [(30,'SalesInvoiceLine',[f'Line ID: {sil[0]}',f'SalesInvoiceID: {inv[0]}']),
                         (740,'SalesInvoice',[f'SalesInvoiceID: {inv[0]}',f'InvoiceDate: {inv[2]}'])]:
        out += [_rect(x,115,500,235,WHITE,RULE,0),_rect(x,115,500,62,BLUE,BLUE,0),_text(x+20,157,title,34,WHITE,'bold')]
        out += [_text(x+20,228+i*62,t,32) for i,t in enumerate(rows)]
    out += [_line(532,285,738,222),_text(625,184,'exact match',29,TEAL,anchor='middle'),
            _text(30,432,'Return the invoice date to the line. The number of lines stays the same.',32,INK)]
    images['chapter-05']['lookup']=_svg('An exact lookup through SalesInvoiceID',
        f'Invoice line {sil[0]} has invoice key {inv[0]}. The matching invoice returns date {inv[2]}.',out,height=480)
    tbl(5,'_merge-check',['Population','Rows','Line total'],[
        ['Source invoice lines',f'{source_count:,}',money(source_total)],
        ['Prepared InvoiceLines',f'{len(lines):,}',money(sum(r['R'] for r in lines))]])
    selected=[r for r in lines if r['fy']==2026];values=[r['R'] for r in selected]
    tbl(6,'_profile',['Fiscal 2026 measure','Value'],[
        ['Invoice lines',f'{len(values):,}'],['Mean line',money(statistics.mean(values))],
        ['Median line',money(statistics.median(values))],['Largest line',money(max(values))]])
    bins=[sum(lo<=v<(lo+1000) for v in values) for lo in range(0,15000,1000)]+[sum(v>=15000 for v in values)]
    csv_out(6,'histogram',['lower_bound','upper_bound_exclusive','invoice_lines'],[(i*1000,(i+1)*1000 if i<15 else '',v) for i,v in enumerate(bins)])
    out=[_text(30,45,'Fiscal 2026 invoice-line amounts',34,BLUE,'bold')]
    top=math.ceil(max(bins)/1000)*1000
    for v in range(0,top+1,1000):
        y=435-330*v/top;out += [_line(115,y,1235,y,RULE),_text(95,y+10,f'{v:,}',28,GRAY,anchor='end')]
    for i,n in enumerate(bins):
        x=115+i*70;h=330*n/top
        out.append(_rect(x,435-h,68,h,BLUE,WHITE,0))
        if i%3==0:out.append(_text(x,480,f'${i}k'+('+' if i==15 else ''),28,GRAY,anchor='middle'))
    out += [_text(30,80,'Number of lines',28,GRAY),_text(30,550,'$1,000 bins. The last bin includes every amount of $15,000 or more.',30,INK)]
    images['chapter-06']['histogram']=_svg('Distribution of invoice-line amounts','A right-skewed distribution with a long upper tail. Bins reconcile to the fiscal 2026 line count.',out,height=585)
    tbl(6,'_driver-totals',['Furniture','Q3','Q4'],[[label]+[money(bridge['drivers'][f'2026-Q{q}'][key]) for q in (3,4)] for label,key in [('Revenue','R'),('Standard cost','C'),('Promotion discounts','D')]])
    effects=[('Volume','volume'),('Mix at list margin','mix'),('Price-list reductions','price lists'),('Promotions','promotions'),('Standard cost change','cost')]
    tbl(6,'_bridge',['Effect on margin dollars','Q3 to Q4'],[[label,money(bridge[key])] for label,key in effects])
    tbl(6,'_margin-rates',['Furniture margin rate','Q3','Q4'],[[label]+[percent(fn(bridge['drivers'][f'2026-Q{q}'])) for q in (3,4)] for label,fn in [('After promotions',lambda s:(s['R']-s['C'])/s['R']),('Before promotions',lambda s:(s['R']+s['D']-s['C'])/(s['R']+s['D']))]])
    out=[_text(30,45,'Furniture margin bridge at standard cost',34,BLUE,'bold')]
    items=[('Q3',bridge['q3'])]+[(label,bridge[key]) for label,key in effects]+[('Q4',bridge['q4'])]
    high=math.ceil(max(bridge['q3'],bridge['q4'])*1.1/100000)*100000
    y=lambda v:435-330*v/high
    running=0
    for i,(label,value) in enumerate(items):
        start=0 if i in (0,6) else running;end=value if i in (0,6) else running+value
        x=75+i*173;upper=max(start,end);lower=min(start,end)
        color=BLUE if i in (0,6) else TEAL if value>=0 else '#B03A2E'
        if i: out.append(_line(x-48,y(start if i<6 else running),x,y(start if i<6 else running),GRAY))
        out += [_rect(x,y(upper),125,max(y(lower)-y(upper),2),color,color,0,width=1),
                _text(x+62,y(upper)-15,f'{value/1000:+.1f}k' if i not in (0,6) else f'${value/1000:.1f}k',28,INK,anchor='middle')]
        short=['Q3','Volume','Mix','Price lists','Promotions','Cost','Q4'][i]
        out.append(_text(x+62,481,short,28,GRAY,anchor='middle'))
        running=end
    out.append(_text(30,552,'Each effect reconciles Q3 margin dollars to Q4. Cost is constant by construction.',30,INK))
    images['chapter-06']['bridge']=_svg('Furniture margin bridge','Promotions reduce margin, with smaller offsetting effects. Exact amounts are in the native effect table.',out,height=590)
    ys=[v for _,v in months];r_all=calc.regression(list(range(1,37)),ys);r_no=calc.regression(list(range(2,37)),ys[1:])
    labels=[m if i in (0,12,24,35) else '' for i,(m,_) in enumerate(months)]
    monthly_top=math.ceil(max(ys)/1e6)
    images['chapter-07']['monthly']=line_chart('Monthly invoiced revenue and fitted trends',labels,[
        ('Observed',[v/1e6 for v in ys],BLUE,False),('All months',[(r_all['a']+r_all['b']*i)/1e6 for i in range(1,37)],GRAY,True),
        ('Without first month',[(r_no['a']+r_no['b']*i)/1e6 for i in range(1,37)],TEAL,'3 7')],
        unit='$ millions',top=monthly_top,ticks=list(range(monthly_top+1)),note='January 2024 is the start-up month. A fitted line is not a forecast validation.')
    csv_out(7,'monthly',['month','invoiced_revenue'],months)
    tbl(7,'_regressions',['Trend fit','R squared','Slope p-value'],[['All 36 months',f'{r_all["r2"]:.3f}',f'{r_all["p_b"]:.3f}'],['Without January 2024',f'{r_no["r2"]:.3f}',f'{r_no["p_b"]:.3f}']])
    tbl(7,'_backtest',['Forecast method','Quarter error','Monthly MAPE'],[[name,f'{err:+.2%}',percent(mape)] for name,(err,mape) in backtest['errors'].items()])
    g='Furniture';static=budget[g,'static Revenue']-budget[g,'static COGS'];flex=budget[g,'flex']-budget[g,'cost'];actual=budget[g,'actual']-budget[g,'cost']
    tbl(7,'_budget',['Furniture FY2026','Margin at standard cost'],[['Static budget',money(static)],['Sales-volume variance',money(flex-static)],['Flexible budget',money(flex)],['Flexible-budget variance',money(actual-flex)],['Actual',money(actual)]])
    scenarios=[('End the promotion',0,0),('Repeat as in 2026',.1,0),('10% discount, 15% lift',.1,.15),('15% discount, 15% lift',.15,.15)]
    tbl(7,'_scenarios',['Scenario','Contribution difference'],[[label,money(model['with'](d,lift)-model['without'])] for label,d,lift in scenarios])
    totals=sum(p['amount'] for p in payments)
    tbl(8,'_payment-control',['Population through 2026','Count','Cash credits / payments'],[['Supplier payments',f'{len(payments):,}',money(totals)],['Related cash postings',f'{len(payments):,}',money(totals)]])
    samples={'All payments':[r['amount'] for r in payments],'Full payments':[r['amount'] for r in payments if r['amount']==r['total']], 'Partial payments':[r['amount'] for r in payments if r['amount']<r['total']]}
    digit={k:calc.benford(v) for k,v in samples.items()}
    tbl(8,'_benford',['Population','First-digit MAD','Book interpretation'],[[k,f'{v["mad"]:.5f}',calc.conformity(v['mad'])] for k,v in digit.items()])
    images['chapter-08']['benford']=line_chart('Full and partial payments have different digit patterns',[str(i) for i in range(1,10)],
        [('Full payments',[digit['Full payments']['actual'][i]*100 for i in range(1,10)],BLUE,False),
         ('Partial payments',[digit['Partial payments']['actual'][i]*100 for i in range(1,10)],TEAL,'3 7'),
         ('Benford expected',[digit['All payments']['expected'][i]*100 for i in range(1,10)],GRAY,True)],
        unit='Percent of payments',top=35,ticks=[0,10,20,30],note='First significant digit. Nonconformity prompts investigation; it does not establish fraud.')
    csv_out(8,'benford',['digit','expected','full_payments','partial_payments'],[(i,digit['All payments']['expected'][i],digit['Full payments']['actual'][i],digit['Partial payments']['actual'][i]) for i in range(1,10)])
    tbl(8,'_aging',['At December 31, 2026','Invoices','Open balance'],[[label,f'{aging["buckets"][label][0]:,}',money(aging['buckets'][label][1])] for _,label in calc.BUCKETS])
    tbl(8,'_ar-reconcile',['Receivables reconciliation','Amount'],[['Open invoice detail',money(aging['subledger'])],['Account 1020 balance',money(aging['gl'])],['Difference to investigate',money(aging['gl']-aging['subledger'])]])
    scores=calc.Counter(j['score'] for j in journals)
    tbl(8,'_scores',['Flags per entry','Entries'],[[score,f'{scores[score]:,}'] for score in sorted(scores)])
    for chapter,figures in images.items():
        for name,doc in figures.items():
            ET.fromstring(doc);path=folders[chapter]/(name+'.svg');path.write_text(doc,encoding='utf-8')
            subprocess.run([renderer,'--format','png','--width','2560','--output',str(path.with_suffix('.png')),str(path)],check=True)
    facts_data={
        'chapter-04':{'control_totals':dict(rows=source_count,line_total=source_total,invoice_subtotal=invoice_total)},
        'chapter-05':{'merge':dict(source_rows=source_count,prepared_rows=len(lines),source_total=source_total,prepared_total=sum(r['R'] for r in lines))},
        'chapter-06':{'bridge':bridge,'histogram':bins,'variables':dict(margin_change=money(bridge['q4']-bridge['q3']))},
        'chapter-07':{'monthly':months,'backtest':backtest,'budget':dict(static=static,flex=flex,actual=actual),
                       'model':{k:v for k,v in model.items() if k!='with'},'variables':dict(break_even_lift=percent(model['breakeven']))},
        'chapter-08':{'payment_count':len(payments),'payment_total':totals,'benford':digit,'aging':aging,'journal_scores':scores,
                       'variables':dict(ar_difference=money(aging['gl']-aging['subledger']))},
    }
    for chapter,folder in folders.items():
        facts={'schema_version':1,'dataset':pin,'generator_sha256':{n:_content_hash(root/n) for n in GENERATORS},
               'artifact_sha256':{n:_content_hash(folder/n) for n in ASSETS[chapter]},**facts_data[chapter]}
        (folder/'facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Refreshed public Chapters 4-8 exhibits; dataset checksum unchanged.')


if __name__=='__main__': refresh(ROOT)
