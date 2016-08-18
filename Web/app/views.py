import ast
import tempfile
from flask import render_template, redirect, request, url_for, send_file, send_from_directory
from app import app, variants, variants_cursor, maps, queries, queries_cursor
from .forms import BuilderForm, QueryForm, SearchForm, ColumnForm
from MySQL_Utils import query_sql, insert_sql
from maps import Maps
from SQLtoVCF import SQLtoVCF
from collections import defaultdict


@app.route('/')
@app.route('/index')
def index():
    form = SearchForm()
    return render_template('search.html', form=form)


@app.route('/sql_to_vcf/', methods=['GET', 'POST'])
def sql_to_vcf():
    vcf = SQLtoVCF(request.args['submit'], str(queries_cursor.lastrowid), 1, 0)
    return send_from_directory('static', vcf.sql_to_vcf())


@app.route('/results/', methods=['GET', 'POST'])
def results():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results', query=form.input_query.data))
    query = request.args['query']
    results = query_sql(query, variants, variants_cursor)
    results = [list(r) for r in results] if results is not None else results
    fields = [i[0] for i in variants_cursor.description]
    if results is not None and len(results) > 0:
        t = fields.index('TYPE') if 'TYPE' in fields else -1
        f = fields.index('FILTER') if 'FILTER' in fields else -1
        g = fields.index('GT') if 'GT' in fields else -1
        s = fields.index('sample_id') if 'sample_id' in fields else -1
        id_map = Maps(variants, variants_cursor, 0)
        id_map.gen_dicts()
        for i in range(len(results)):
            if t > -1:
                results[i][t] = id_map.variant_mapping[results[i][t]] if results[i][t] in id_map.variant_mapping else 'None'
            if f > -1:
                results[i][f] = id_map.filter_mapping[results[i][f]] if results[i][f] in id_map.filter_mapping else 'None'
            if g > -1:
                results[i][g] = id_map.genotype_mapping[results[i][g]] if results[i][g] in id_map.genotype_mapping else 'None'
            if s > -1:
                results[i][s] = id_map.sample_mapping[results[i][s]] if results[i][s] in id_map.sample_mapping else 'None'
        insert_sql("queries ", ["query"], [query], queries, queries_cursor)
        results = sorted(results, key=lambda element: (element[0], element[1]))
    return render_template('results.html', form=form, fields=fields, results=results, query=query)


@app.route('/query', methods=['GET', 'POST'])
def query():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results', query=form.input_query.data))
    return render_template('query.html', form=form)


@app.route('/library', methods=['GET', 'POST'])
def library():
    results = query_sql("select time, query from queries", queries, queries_cursor)
    results = [[v for v in r] for r in results] if results is not None else results
    fields = [i[0] for i in queries_cursor.description]
    return render_template('library.html', fields=fields, results=results)


@app.route('/build/')
def build():
    query = []
    types = ast.literal_eval(request.args['types'])
    genotypes = ast.literal_eval(request.args['genotypes'])
    tumor = request.args['tumor'] if request.args['tumor'] == 'True' else ''
    samples = ast.literal_eval(request.args['samples'])
    breeds = ast.literal_eval(request.args['breeds'])
    tools = ast.literal_eval(request.args['tools'])
    tool_filters = ast.literal_eval(request.args['tool_filters'])
    columns = ast.literal_eval(request.args['columns'])
    regions = ast.literal_eval(request.args['regions'])
    type_vals = types.values()
    type_keys = types.keys()
    types = ["type = '%s'" % (maps.variant_mapping[type_keys[i]]) for i in range(len(type_vals)) if type_vals[i]]
    gt_vals = genotypes.values()
    gt_keys = genotypes.keys()
    genotypes = ["g.gt = '%s'" % (maps.genotype_mapping[gt_keys[i]]) for i in range(len(gt_vals)) if gt_vals[i] == 1]
    samples = ["g.sample_id = '%s'" % (maps.sample_mapping[sample]) for sample in samples]
    breeds = ["breed_type = '%s'" % (maps.breed_mapping[breed]) for breed in breeds]
    tools = ["t.tool = '%s'" % (maps.tool_mapping[maps.tool_name_mapping[tool]]) for tool in tools]
    regions = ["(%s)" % region.replace(" is ", "=") for region in regions]
    necessary_joins = []

    filters = defaultdict(list)
    for f in tool_filters:
        table = f.split(".")[0]
        filters[table].append(f.split(".")[1])
        if table not in necessary_joins:
            necessary_joins.append(table)
    for c in columns:
        table = c.split(".")[0]
        if table not in necessary_joins:
            necessary_joins.append(table)
    
    if "r" in necessary_joins:
        necessary_joins.remove("r")
    '''TODO: distill necessary joins to just the list, with no ancillary checks'''

    if len(samples) > 0 or len(genotypes) > 0 or "g" in necessary_joins or "s" in necessary_joins:
        g = 'INNER JOIN genotype g on g.record_id=r.id '
        if len(samples) > 0:
            g = '%s and (%s) ' % (g, ' or '.join(samples))
        if len(genotypes) > 0:
            g = '%s and (%s)' % (g, ' or '.join(genotypes))
        query.append(g)
        if "g" in necessary_joins:
            necessary_joins.remove("g")

    if len(breeds) > 0 or "s" in necessary_joins:
        s = 'INNER JOIN samples s on s.sample_id=g.sample_id '
        if len(breeds) > 0:
            s = '%sand individual_id in (select individual_id from individuals where %s)' % (s, ' or '.join(breeds))
        query.append(s)
        necessary_joins.remove("s")

    if len(tools) > 0:
        query.append('INNER JOIN tools_used t on t.record_id=r.id and %s' % (' or '.join(tools)))

    if len(necessary_joins) > 0:
        for j in necessary_joins:
            f = 'INNER JOIN %s on %s.record_id=r.id ' % (j, j)
            if len(filters.keys()) > 0:
                f = '%s and (%s)' % (f, ' and '.join(filters[j]))
            query.append(f)

    core = []
    if len(filters['r']) > 0:
        core.append(' and '.join(filters['r']))
    if len(types) > 0:
        core.append('(%s)' % ' or '.join(types))
    if len(regions) > 0:
        core.append('(%s)' % ' or '.join(regions))
    if len(core) > 0:
        query.append('where %s' % ' and '.join(core))

    cols = []
    if len(columns) > 0:
        cols.append(', '.join(columns))
    if len(cols) == 0:
        cols = ['chrom,pos,filter,type,chrom2,pos2,len']

    query = "select %s from records r %s limit 5000" % (', '.join(cols), ' '.join(query))
    return redirect(url_for('results', query=query))


@app.route('/builder', methods=['GET', 'POST'])
def builder():
    form = BuilderForm(prefix="form")
    cols = ColumnForm(prefix="cols")
    if request.method == 'POST':
        form.breed_include.choices = [(str(b), str(b)) for b in form.breed_include.data] 
        form.sample_include.choices = [(str(b), str(b)) for b in form.sample_include.data] 
        form.tool_include.choices = [(str(b), str(b)) for b in form.tool_include.data]
        form.region_include.choices = [(str(b), str(b)) for b in form.region_include.data]
        form.breed_exclude.choices = [(str(b), str(b)) for b in form.breed_exclude.data] 
        form.sample_exclude.choices = [(str(b), str(b)) for b in form.sample_exclude.data] 
        form.tool_exclude.choices = [(str(b), str(b)) for b in form.tool_exclude.data]
        form.region_exclude.choices = [(str(b), str(b)) for b in form.region_exclude.data]
        form.tool_clauses.choices = [(str(b),str(b)) for b in form.tool_clauses.data]

        cols.columns_include.choices = [(str(b), str(b)) for b in cols.columns_include.data]
        cols.columns_exclude.choices = [(str(b), str(b)) for b in cols.columns_exclude.data]
        if form.validate_on_submit():
            types = {
                'DEL': form.DEL.data,
                'DUP': form.DUP.data,
                'INS': form.INS.data,
                'INV': form.INV.data,
                'TRA': form.TRA.data,
                'SIN': form.SIN.data,
                'LIN': form.LIN.data,
                'BXP': form.BXP.data
            }
            genotypes = {
                '0/0': form.homref.data,
                '0/1': form.het.data,
                '1/1': form.homalt.data
            }
            regions = form.region_include.data,
            tumor = form.tumor.data
            samples = form.sample_include.data, 
            breeds = form.breed_include.data,     # adding a comma here avoids a bad request
            tools = form.tool_include.data,       # adding a comma here avoids a bad request
            tool_filters = '["' + '", "'.join(form.tool_clauses.data) + '"]' \
                if len(form.tool_clauses.data) > 0 else '[]'
            columns = cols.columns_include.data,
            return redirect(url_for('build', types=types, genotypes=genotypes,
                                    regions=regions, tumor=tumor, samples=samples,
                                    breeds=breeds, tools=tools, tool_filters=tool_filters, columns=columns))

    sql = "SELECT Unabbreviated FROM ref_breed"
    if form.breed_include.choices is not None:
        form.breed_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)
                                      if (b[0], b[0]) not in form.breed_include.choices]
    else:
        form.breed_exclude.choices = [(b[0],b[0]) for b in query_sql(sql, variants, variants_cursor)]
    sql = "SELECT sample FROM ref_sample"
    if form.sample_include.choices is not None:
        form.sample_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)
                                       if (b[0], b[0]) not in form.sample_include.choices]
    else:
        form.sample_exclude.choices = [(b[0],b[0]) for b in query_sql(sql, variants, variants_cursor)]
    sql = "SELECT Unabbreviated FROM ref_tool"
    if form.tool_include.choices is not None:
        form.tool_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)
                                     if (b[0], b[0]) not in form.tool_include.choices]
    else:
        form.tool_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)]

    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'records'"
    records = [b[0] for b in query_sql(sql, variants, variants_cursor)]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'samples'"
    samples = [b[0] for b in query_sql(sql, variants, variants_cursor)]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'genotype'"
    genotypes = [b[0] for b in query_sql(sql, variants, variants_cursor)]

    sql = "SELECT tool FROM ref_tool"
    tools = [b[0].lower() for b in query_sql(sql, variants, variants_cursor)]
    tables = [b[0] for t in tools for b in
              query_sql("SELECT table_name from information_schema.tables where table_name like '%s_%%'" % t,
                        variants, variants_cursor)]
    tool_columns = {}
    tool_types = {}
    for t in tables:
        table_cols = []
        col_type = []
        sql = "SELECT column_name from information_schema.columns where table_name = '%s'" % t
        for b in query_sql(sql, variants, variants_cursor):
            table_cols.append(b[0])
        sql = "SELECT data_type from information_schema.columns where table_name = '%s'" % t
        for d in query_sql(sql, variants, variants_cursor):
            if "int" in d[0]:
                col_type.append("num")
            elif "float" in d[0]:
                col_type.append("num")
            elif "varchar" in d[0]:
                col_type.append("str")
            else:
                col_type.append(d[0])
        tool_columns.update({t: table_cols})
        tool_types.update({t: col_type})
    return render_template('builder.html', form=form, cols=cols, tools=tools,
                           tool_columns=tool_columns, tool_types=tool_types, records=records,
                           samples=samples, genotypes=genotypes)