"""Build the portable Tableau workbook from the template and aggregate CSVs."""
from pathlib import Path
from copy import deepcopy
from datetime import date
import csv
import tempfile
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as ET
from tableauhyperapi import HyperProcess, Telemetry, Connection, CreateMode, TableDefinition, TableName, SqlType, Inserter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard"
DATA = ROOT / "outputs/tableau"
STATE = "federated.1u2efw001eayuc1b26b3f1cvisw0"
KPI = "federated.0n6jrm1145x01b10n5ev31i1sjlh"
TREND = "federated.olist_monthly"
CATEGORY = "federated.olist_categories"
REVIEW = "federated.olist_reviews"
PAGE1 = "Where Should Olist Grow Next?"
PAGE2 = "Growth & Customer Experience"
BLUE = "#356a91"
TEAL = "#238b87"
ORANGE = "#d47a29"
RATE_MAP = {"late_delivery_rate_pct": "late_delivery_rate", "negative_review_rate_pct": "negative_review_rate", "order_growth_pct": "order_growth_rate"}
CAPTIONS = {"product_revenue": "Product Value (BRL)", "avg_order_value": "Avg Order Value (BRL)", "baseline_score": "Opportunity Score", "negative_review_rate": "Negative Review Rate", "order_month": "Purchase Month", "comparable_revenue": "Product Value (BRL)", "delivery_status": "Status", "trend_value": "Orders / Product Value (BRL)", "year_filter": "Year Selection", "revenue_2017": "Product Value 2017 (BRL)", "revenue_2018": "Product Value 2018 (BRL)", "revenue_change": "Product Value Change (BRL)", "revenue_growth_rate": "Product Value Growth Rate"}


def sub(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def fmt(parent, attr, value, **attrs):
    return sub(parent, 'format', attr=attr, value=value, **attrs)


def cap(name):
    return CAPTIONS.get(name, name.replace('_', ' ').title())


def dtype(name, rows):
    if name in ('analysis_start', 'analysis_end', 'order_month'):
        return 'date'
    if name in ('state', 'recommendation', 'risk_flag', 'product_category', 'delivery_status'):
        return 'string'
    if name in ('baseline_rank', 'delivered_orders', 'reviewed_orders', 'late_orders', 'negative_reviews', 'orders_2017', 'orders_2018', 'order_change', 'comparable_orders'):
        return 'integer'
    return 'real'


def col(parent, name, typ):
    numeric = typ in ('integer', 'real')
    c = sub(parent, 'column', name=f'[{name}]', caption=cap(name), datatype=typ,
            role='measure' if numeric else 'dimension', type='quantitative' if numeric else 'ordinal' if typ == 'date' else 'nominal')
    if name.endswith('_rate'):
        c.set('default-format', 'p0.00%')
    elif any(v in name for v in ('revenue', 'order_value')):
        c.set('default-format', 'c"R$ "#,##0.00;-"R$ "#,##0.00')
    elif typ == 'integer':
        c.set('default-format', 'n#,##0')
    elif name in ('baseline_score', 'avg_delivery_days', 'avg_review_score', 'orders_per_seller'):
        c.set('default-format', 'n0.00')
    return c


def datasource(template, ds_name, filename, rows, types):
    ds = deepcopy(template)
    ds.set('name', ds_name)
    ds.set('caption', filename.removesuffix('.csv'))
    old = 'tableau_kpis.csv'
    object_id = filename + '_olist'
    connection_name = 'textscan.' + filename.removesuffix('.csv')
    for e in ds.iter():
        for key, value in list(e.attrib.items()):
            value = value.replace('tableau_kpis.csv_BEC55B9FDA65499E99C3A5EB76224213', object_id)
            value = value.replace(old, filename).replace('tableau_kpis#csv', filename.replace('.csv', '#csv'))
            value = value.replace('textscan.0s96jzo051r9zd1gkli611p9oeem', connection_name)
            e.set(key, value)
    for c in ds.findall('column'):
        ds.remove(c)
    for conn in ds.findall('.//connection[@class="textscan"]'):
        conn.set('directory', 'Data')
        conn.set('filename', filename)
    for conn in ds.findall('.//connection[@class="hyper"]'):
        conn.set('dbname', 'Data/' + filename.replace('.csv', '.hyper'))
        conn.attrib.pop('update-time', None)
    for cols in ds.findall('.//columns'):
        cols[:] = []
        for i, (name, typ) in enumerate(types.items()):
            sub(cols, 'column', name=name, datatype=typ, ordinal=i)
    for records in ds.findall('.//metadata-records'):
        sample = deepcopy(records.find('metadata-record[@class="column"]'))
        records[:] = []
        extracted = records.getparent().get('class') == 'hyper'
        for i, (name, typ) in enumerate(types.items()):
            rec = deepcopy(sample)
            for field, val in {'remote-name':name, 'local-name':f'[{name}]', 'remote-alias':name,
                               'ordinal':str(i), 'local-type':typ, 'remote-type':{'date':'133','string':'129','integer':'20','real':'5'}[typ],
                               'aggregation':'Sum' if typ in ('integer','real') else 'Year' if typ == 'date' else 'Count',
                               'parent-name':'[Extract]' if extracted else f'[{filename}]', 'object-id':f'[{object_id}]'}.items():
                node = rec.find(field)
                if node is not None:
                    node.text = val
            records.append(rec)
    insert_at = ds.index(ds.find('extract'))
    for name, typ in types.items():
        c = col(ET.Element('holder'), name, typ)
        ds.insert(insert_at, c)
        insert_at += 1
    sv = ds.find('semantic-values')
    if sv is not None:
        ds.remove(sv)
    return ds


def add_calc(ds, name, typ, formula):
    c = col(ET.Element('holder'), name, typ)
    sub(c, 'calculation', **{'class':'tableau', 'formula':formula})
    ds.insert(ds.index(ds.find('extract')), c)
    return c


def instance(name, typ):
    return f'[sum:{name}:qk]' if typ in ('integer','real') else f'[tmn:{name}:qk]' if typ == 'date' else f'[none:{name}:nk]'


def sheet(name, ds, types, x, y, mark, label=None, tooltips=(), sort=False, color=BLUE):
    w = ET.Element('worksheet', name=name)
    title = sub(sub(sub(w, 'layout-options'), 'title'), 'formatted-text')
    sub(title, 'run', fontname='Arial', fontsize='13', bold='true').text = name
    t = sub(w, 'table')
    view = sub(t, 'view')
    sub(sub(view, 'datasources'), 'datasource', name=ds.get('name'), caption=ds.get('caption'))
    dep = sub(view, 'datasource-dependencies', datasource=ds.get('name'))
    fields = list(dict.fromkeys([x, y] + ([label] if label else []) + list(tooltips)))
    for field in fields:
        c = ds.find(f'column[@name="[{field}]"]')
        dep.append(deepcopy(c))
        typ = types[field]
        sub(dep, 'column-instance', column=f'[{field}]', derivation='Sum' if typ in ('integer','real') else 'Month-Trunc' if typ == 'date' else 'None',
            name=instance(field, typ), pivot='key', type='quantitative' if typ in ('integer','real','date') else 'nominal')
    ref = lambda f: f'[{ds.get("name")}].{instance(f, types[f])}'
    if sort:
        sub(sub(view, 'shelf-sorts'), 'shelf-sort-v2', dimension_to_sort=ref(y), direction='DESC',
            is_on_innermost_dimension='true', measure_to_sort_by=ref(x), shelf='rows')
    sub(view, 'aggregation', value='true')
    style = sub(t, 'style')
    axes = sub(style, 'style-rule', element='axis')
    for f, scope in ((x, 'cols'), (y, 'rows')):
        if types[f] in ('real','integer'):
            fmt(axes, 'title', cap(f), field=ref(f), scope=scope, **{'class':'0'})
    pane = sub(sub(t, 'panes'), 'pane', selection_relaxation_option='selection-relaxation-allow')
    sub(sub(pane, 'view'), 'breakdown', value='auto')
    sub(pane, 'mark', **{'class':mark})
    enc = sub(pane, 'encodings')
    if label:
        sub(enc, 'text', column=ref(label))
    for field in tooltips:
        sub(enc, 'tooltip', column=ref(field))
    rule = sub(sub(pane, 'style'), 'style-rule', element='mark')
    fmt(rule, 'mark-color', color)
    fmt(rule, 'mark-labels-show', 'true' if label else 'false')
    fmt(rule, 'mark-labels-cull', 'true')
    sub(t, 'rows').text = ref(y)
    sub(t, 'cols').text = ref(x)
    return w


def parameter(name, choices, default):
    c = ET.Element('column', {'name':f'[{name}]', 'caption':name, 'datatype':'string', 'param-domain-type':'list',
                             'role':'measure', 'type':'nominal', 'value':f'"{default}"'})
    sub(c, 'calculation', **{'class':'tableau','formula':f'"{default}"'})
    members = sub(c, 'members')
    for choice in choices:
        sub(members, 'member', value=f'"{choice}"')
    return c


def zone(parent, zid, x, y, w, h, **attrs):
    z = sub(parent, 'zone', id=zid, x=round(x/1200*100000), y=round(y/900*100000),
            w=round(w/1200*100000), h=round(h/900*100000), **attrs)
    return z


def textzone(parent, zid, x,y,w,h, text, size=10, bold=False, color='#303b42'):
    z = zone(parent,zid,x,y,w,h,type_v2='text')
    sub(sub(z,'formatted-text'),'run',fontname='Arial',fontsize=size,bold=str(bold).lower(),fontcolor=color).text=text
    fmt(sub(z,'zone-style'), 'margin', '6')
    return z


def dashboard(name):
    d = ET.Element('dashboard', name=name)
    sub(d,'style')
    sub(d,'size',maxheight=900,maxwidth=1200,minheight=900,minwidth=1200,sizing_mode='fixed')
    zones = sub(d,'zones')
    body = zone(zones,0,0,0,1200,900,type_v2='layout-basic')
    return d, body


def main():
    OUT.mkdir(exist_ok=True)
    tree = ET.parse(str(OUT / 'workbook_template.twb')).getroot()
    template = deepcopy(tree.find(f'./datasources/datasource[@name="{KPI}"]'))
    tree.find('datasources')[:] = []
    inputs = [(STATE,'tableau_state_recommendations.csv'),(KPI,'tableau_kpis.csv'),(TREND,'tableau_monthly_trend.csv'),
              (CATEGORY,'tableau_category_metrics.csv'),(REVIEW,'tableau_delivery_review.csv')]
    records, definitions, sources = {}, {}, {}
    for ds_name, filename in inputs:
        rows = list(csv.DictReader((DATA / filename).open()))
        types = {name:dtype(name,rows) for name in rows[0]}
        records[filename], definitions[ds_name] = rows, types
        ds = datasource(template,ds_name,filename,rows,types)
        sources[ds_name] = ds
        tree.find('datasources').append(ds)
    params = ET.Element('datasource', name='Parameters', inline='true', hasconnection='false', version='18.1')
    params.append(parameter('Trend Metric', ['Delivered orders','Product value (BRL)'], 'Delivered orders'))
    params.append(parameter('Trend Year', ['All','2017','2018'], 'All'))
    tree.find('datasources').insert(0,params)
    trend_ds = sources[TREND]
    add_calc(trend_ds,'trend_value','real','IF [Parameters].[Trend Metric] = "Delivered orders" THEN [delivered_orders] ELSE [product_revenue] END')
    add_calc(trend_ds,'year_filter','boolean','[Parameters].[Trend Year] = "All" OR STR(YEAR([order_month])) = [Parameters].[Trend Year]')
    definitions[TREND].update(trend_value='real',year_filter='boolean')
    cat_rows = records['tableau_category_metrics.csv']
    top = sorted(cat_rows,key=lambda r:float(r['comparable_revenue']),reverse=True)[:10]
    top_formula = '[product_category] IN (' + ','.join('"'+r['product_category']+'"' for r in top) + ')'
    add_calc(sources[CATEGORY],'top_ten','boolean',top_formula)

    # Preserve the original worksheets while migrating state rate units.
    worksheets = tree.find('worksheets')
    for ws in worksheets:
        for e in ws.iter():
            for k,v in list(e.attrib.items()):
                for old,new in RATE_MAP.items(): v=v.replace(old,new)
                v=v.replace('Late Delivery Rate Pct','Late Delivery Rate').replace('Negative Review Rate Pct','Negative Review Rate').replace('Order Growth Pct','Order Growth Rate')
                e.set(k,v)
            if e.text:
                for old,new in RATE_MAP.items(): e.text=e.text.replace(old,new)
        for dep in ws.findall('.//datasource-dependencies'):
            ds=sources[dep.get('datasource')]
            for c in dep.findall('column'):
                replacement=ds.find(f'column[@name="{c.get("name")}"]')
                if replacement is not None:
                    dep.replace(c,deepcopy(replacement))
        for run in ws.findall('.//layout-options/title/formatted-text/run'):
            run.set('fontname','Arial')
            run.set('fontsize','13')
        for title in ws.findall('.//format[@attr="title"]'):
            title.set('value',title.get('value').replace('\u2013','-'))
        if ws.get('name') == 'Market Scale vs Delivery Risk':
            for enc in ws.findall('.//encodings/size'):
                enc.getparent().remove(enc)
        for title in ws.findall('./layout-options/title/formatted-text'):
            title[:] = []
            sub(title,'run',fontname='Arial',fontsize=13,bold='true').text=ws.get('name')
        if ws.get('name') == 'State Opportunity Ranking':
            axes = ws.find('./table/style/style-rule[@element="axis"]')
            sub(axes, 'encoding', attr='space', **{'class':'0', 'field':f'[{STATE}].[sum:baseline_score:qk]',
                'field-type':'quantitative', 'min':'0', 'max':'100', 'range-type':'fixed', 'scope':'cols', 'type':'space'})
            mark_style = ws.find('./table/panes/pane/style/style-rule[@element="mark"]')
            fmt(mark_style, 'font-size', '9')
            mark_style.find('format[@attr="mark-labels-cull"]').set('value', 'false')
    sheets = [
        sheet('Monthly Delivered Orders and Product Value',trend_ds,definitions[TREND], 'order_month','trend_value','Line',tooltips=('delivered_orders','product_revenue','avg_order_value')),
        sheet('Top 10 Categories by Product Value',sources[CATEGORY],definitions[CATEGORY], 'comparable_revenue','product_category','Bar',sort=True,tooltips=('revenue_2017','revenue_2018','revenue_growth_rate','orders_2017','orders_2018'),color=TEAL),
        sheet('Late Delivery and Negative Reviews',sources[REVIEW],definitions[REVIEW], 'negative_review_rate','delivery_status','Bar',label='negative_review_rate',tooltips=('reviewed_orders','negative_reviews','avg_review_score'),color=ORANGE)]
    for w in sheets: worksheets.append(w)
    for w,ds,field in [(sheets[0],trend_ds,'year_filter'),(sheets[1],sources[CATEGORY],'top_ten')]:
        view=w.find('./table/view'); dep=view.find('datasource-dependencies')
        dep.append(deepcopy(ds.find(f'column[@name="[{field}]"]')))
        sub(dep,'column-instance',column=f'[{field}]',derivation='None',name=f'[none:{field}:nk]',pivot='key',type='nominal')
        f=ET.Element('filter',{'class':'categorical','column':f'[{ds.get("name")}].[none:{field}:nk]'})
        sub(f,'groupfilter',function='member',level=f'[none:{field}:nk]',member='true')
        before = view.find('shelf-sorts')
        if before is None:
            before = view.find('aggregation')
        view.insert(view.index(before),f)
    trend_view=sheets[0].find('./table/view')
    sub(trend_view.find('datasources'),'datasource',name='Parameters')
    pd=sub(ET.Element('holder'),'datasource-dependencies',datasource='Parameters')
    for c in params: pd.append(deepcopy(c))
    trend_view.insert(2,pd)

    # Use a restrained palette consistently across both state worksheets.
    colors={'Core market':BLUE,'Priority expansion':TEAL,'Fix operations first':ORANGE,
            'Pilot / validate data':'#8a939c','Selective expansion / monitor':'#6c8e47'}
    state_style = ET.Element('style')
    enc = sub(sub(state_style, 'style-rule', element='mark'), 'encoding', attr='color',
              field='[none:recommendation:nk]', type='palette')
    for category, color in colors.items():
        sub(sub(enc, 'map', to=color), 'bucket').text='"'+category+'"'
    state_source = sources[STATE]
    color_instance = ET.Element('column-instance', column='[recommendation]', derivation='None',
                                name='[none:recommendation:nk]', pivot='key', type='nominal')
    state_source.insert(state_source.index(state_source.find('extract')), color_instance)
    anchor = state_source.find('layout')
    if anchor is None:
        anchor = state_source.find('extract')
    state_source.insert(state_source.index(anchor) + 1, state_style)

    actions = tree.find('actions')
    if actions is None:
        actions = ET.Element('actions')
        tree.insert(tree.index(worksheets), actions)
    actions[:] = []
    action = sub(actions, 'action', caption='Highlight State', name='[HighlightState]')
    sub(action, 'activation', auto_clear='true', type='on-select')
    sub(sub(action, 'source', dashboard=PAGE1, type='sheet'), 'exclude-sheet', name='KPI Overview')
    command = sub(action, 'command', command='tsc:brush')
    for name, value in [('exclude', 'KPI Overview'), ('field-captions', 'State'), ('target', PAGE1)]:
        sub(command, 'param', name=name, value=value)

    dashboards=tree.find('dashboards'); dashboards[:]=[]
    d,b=dashboard(PAGE1); dashboards.append(d)
    textzone(b,1,16,12,880,42,PAGE1,22,True)
    textzone(b,2,16,54,1168,27,'Brazilian marketplace orders | Historical analysis, 2017-2018 | Liang Yao',10)
    zone(b,3,16,86,1168,90,name='KPI Overview',show_title='false')
    zone(b,4,16,185,840,350,name='State Opportunity Ranking')
    zone(b,5,16,545,840,285,name='Market Scale vs Delivery Risk')
    zone(b,6,880,185,300,148,name='State Opportunity Ranking',type_v2='color',param=f'[{STATE}].[none:recommendation:nk]',pane_specification_id=0)
    textzone(b,7,880,342,300,260,'RECOMMENDED ACTIONS\n\nSP: Defend the core market.\n\nPR and MG: Validate expansion.\n\nRJ and BA: Improve delivery and customer experience before scaling.\n\nDF: Start with a small pilot.',11)
    textzone(b,8,880,612,300,213,'READ THE SCORE WITH CARE\n\nWeights express priorities, not expected profit.\n\nSeller location is a coverage proxy, not capacity.\n\nLow-volume states need more evidence before a large commitment.',10)
    textzone(b,9,16,837,1168,56,'KPI scope: Jan 2017-Aug 2018; delivered orders with actual delivery dates. State scope: Jan-Aug 2017 vs Jan-Aug 2018; 16 states with at least 500 orders. Product value excludes freight and is not Olist platform revenue.',9)

    d,b=dashboard(PAGE2); dashboards.append(d)
    textzone(b,1,16,12,1168,42,PAGE2,22,True)
    textzone(b,2,16,54,1168,30,'Demand grew, but growth alone does not establish where expansion will pay off.',11)
    zone(b,3,16,96,280,68,type_v2='paramctrl',param='[Parameters].[Trend Metric]')
    zone(b,4,316,96,180,68,type_v2='paramctrl',param='[Parameters].[Trend Year]')
    zone(b,5,16,175,1168,260,name=sheets[0].get('name'))
    zone(b,6,16,449,725,326,name=sheets[1].get('name'))
    zone(b,7,766,449,418,185,name=sheets[2].get('name'))
    textzone(b,8,766,640,418,135,'53.98% of reviewed late orders had a negative review, versus 9.17% of on-time orders.\n\nThis association supports investigation; it does not prove that lateness caused the difference.',11)
    textzone(b,9,16,796,1168,95,'Monthly trend: all delivered orders purchased Jan 2017-Aug 2018 (96,211 orders; includes 8 missing delivery dates). Category comparison: Jan-Aug in each year; an order can belong to several categories. Reviews: delivered orders with actual delivery dates and matched reviews; negative = mean order review score <= 2. Rates use their own denominators.',9)

    windows=tree.find('windows'); windows[:]=[]
    for ws in worksheets:
        w=sub(windows,'window',**{'class':'worksheet','name':ws.get('name')})
        sub(w,'cards')
        sub(sub(w,'viewpoint'),'zoom',type='entire-view')
    for name in (PAGE1,PAGE2):
        w=sub(windows,'window',**{'class':'dashboard','name':name})
        if name==PAGE1: w.set('maximized','true')
        views=sub(w,'viewpoints')
        for ws in worksheets:
            sub(sub(views,'viewpoint',name=ws.get('name')),'zoom',type='entire-view')
        sub(w,'active',id=3 if name==PAGE1 else 5)
    for node in list(worksheets) + list(dashboards) + list(windows):
        if node.find('simple-id') is None:
            sub(node,'simple-id',uuid='{'+str(uuid.uuid5(uuid.NAMESPACE_URL, node.tag+node.get('name'))).upper()+'}')
    if tree.find('thumbnails') is not None: tree.remove(tree.find('thumbnails'))
    xml=ET.tostring(tree,encoding='utf-8',xml_declaration=True,pretty_print=True)
    (OUT/'olist_growth_dashboard.twb').write_bytes(xml)
    with tempfile.TemporaryDirectory(prefix='olist-hyper-') as tmp:
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={'log_dir':tmp}) as hp:
            for ds_name,filename in inputs:
                types=definitions[ds_name]
                raw_types={k:v for k,v in types.items() if k in records[filename][0]}
                hyper=Path(tmp)/filename.replace('.csv','.hyper')
                type_map={'date':SqlType.date(),'string':SqlType.text(),'integer':SqlType.big_int(),'real':SqlType.double()}
                table=TableDefinition(TableName('Extract','Extract'),[TableDefinition.Column(k,type_map[t]) for k,t in raw_types.items()])
                with Connection(hp.endpoint,str(hyper),CreateMode.CREATE_AND_REPLACE) as con:
                    con.catalog.create_schema('Extract'); con.catalog.create_table(table)
                    with Inserter(con,table) as ins:
                        for row in records[filename]:
                            values=[]
                            for k,t in raw_types.items():
                                v=row[k]
                                values.append(None if v=='' else date.fromisoformat(v) if t=='date' else int(float(v)) if t=='integer' else float(v) if t=='real' else v)
                            ins.add_row(values)
                        ins.execute()
        with ZipFile(OUT/'olist_growth_dashboard.twbx','w',ZIP_DEFLATED) as z:
            z.writestr('olist_growth_dashboard.twb',xml)
            for _,filename in inputs:
                z.write(DATA/filename,'Data/'+filename)
                hp=filename.replace('.csv','.hyper')
                z.write(Path(tmp)/hp,'Data/'+hp)
    print(OUT/'olist_growth_dashboard.twbx')


if __name__ == '__main__':
    main()
