import ast
from flask import render_template, flash, redirect, request, url_for
from app import app, variants, variants_cursor, maps, queries, queries_cursor
from .forms import BuilderForm, QueryForm, SearchForm, ColumnForm
from MySQL_Utils import executeSQL, querySQL, insertSQL
from collections import defaultdict

@app.route('/')
@app.route('/index')
def index():
    form = SearchForm()
    return render_template('search.html', form=form)

@app.route('/results/', methods=['GET', 'POST'])
def results():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results', query=form.input_query.data))
    query = request.args['query']
    results = querySQL(query, variants, variants_cursor)
    fields = [i[0] for i in variants_cursor.description]
    if results is not None and len(results) > 0:
    	insertSQL("queries", ["query"], [query], queries, queries_cursor)
    	results = sorted(results, key=lambda element: (element[0], element[1]))
    return render_template('results.html', form=form, fields = fields, results=results, query=query)

@app.route('/query', methods=['GET', 'POST'])
def query():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results', query=form.input_query.data))
    return render_template('query.html', form=form)

@app.route('/build/')
def build():
    query = []
    records =  ast.literal_eval(request.args['records'])
    types = ast.literal_eval(request.args['types'])
    genotypes = ast.literal_eval(request.args['genotypes'])
    tumor = request.args['tumor'] if request.args['tumor'] == 'True' else ''
    samples = ast.literal_eval(request.args['samples'])
    breeds = ast.literal_eval(request.args['breeds'])
    tools = ast.literal_eval(request.args['tools'])
    tool_filters = ast.literal_eval(request.args['tool_filters'])
    columns = ast.literal_eval(request.args['columns'])
    regions = ast.literal_eval(request.args['regions'])
    recVals = records.values()
    recKeys = records.keys()
    records = ["%s = '%s'" % (recKeys[i], recVals[i]) for i in range(len(recVals)) if recVals[i] is not None and len(str(recVals[i])) > 0]
    typeVals = types.values()
    typeKeys = types.keys()
    types = ["type = '%s'" % (maps.variant_mapping[typeKeys[i]]) for i in range(len(typeVals)) if typeVals[i]]
    gtVals = genotypes.values()
    gtKeys = genotypes.keys()
    genotypes = ["g.gt = '%s'" % (maps.genotype_mapping[gtKeys[i]]) for i in range(len(gtVals)) if gtVals[i] == 1]
    samples = ["g.sample_id = '%s'" % (maps.sample_mapping[sample]) for sample in samples]
    breeds = ["breed_type = '%s'" % (maps.breed_mapping[breed]) for breed in breeds]
    tools = ["t.tool = '%s'" % (maps.tool_mapping[maps.tool_name_mapping[tool]]) for tool in tools]
    regions = ["(%s)" % region.replace(" is ", "=") for region in regions]
    
    print query
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
    print necessary_joins
    necessary_joins.remove("r")
    #distill necessary joins to just the list, with no ancillary checks


    if len(samples) > 0 or len(genotypes) > 0 or "g" in necessary_joins or "s" in necessary_joins:
    	g = 'INNER JOIN genotype g on g.record_id=r.id '
    	if len(samples) > 0:
        	g = '%s and (%s) ' % (g, ' or '.join(samples))
    	if len(genotypes) > 0:
        	g = '%s and (%s)' % (g, ' or '.join(genotypes))
        query.append(g)
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
    if len(records) > 0:
    	core.append(' and '.join(records))
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
    	cols = ['*']

    query = "select %s from records r %s limit 5000" % (', '.join(cols), ' '.join(query))
    print query
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
            records = {
            'ref':form.ref.data, 
            'alt':form.alt.data, 
            'qual':form.alt.data, 
            'filter':form.filter.data, 
            'len':form.len.data, 
            }
            types = {
            'DEL':form.DEL.data, 
            'DUP':form.DUP.data, 
            'INS':form.INS.data,
            'INV':form.INV.data, 
            'TRA':form.TRA.data, 
            'SIN':form.SIN.data, 
            'LIN':form.LIN.data, 
            'BXP':form.BXP.data
            }
            genotypes = {
            '0/0':form.homref.data, 
            '0/1':form.het.data, 
            '1/1':form.homalt.data
            }
            regions = form.region_include.data,
            tumor = form.tumor.data
            samples = form.sample_include.data, 
            breeds = form.breed_include.data,     #adding a comma here avoids a bad request
            tools = form.tool_include.data,        #adding a comma here avoids a bad request
            tool_filters = '["' + '", "'.join(form.tool_clauses.data) + '"]' if len(form.tool_clauses.data) > 0 else '[]'
            columns = cols.columns_include.data,
            return redirect(url_for('build', records=records, types=types, genotypes=genotypes, regions=regions, tumor=tumor, samples=samples, breeds=breeds, tools=tools, tool_filters=tool_filters, columns=columns))

    sql = "SELECT Unabbreviated FROM ref_breed"
    if form.breed_include.choices is not None:
    	form.breed_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, variants, variants_cursor) if (b[0],b[0]) not in form.breed_include.choices]
    else:
    	form.breed_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, variants, variants_cursor)]
    sql = "SELECT sample FROM ref_sample"
    if form.sample_include.choices is not None:
    	form.sample_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, variants, variants_cursor) if (b[0],b[0]) not in form.sample_include.choices]
    else:
    	form.sample_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, variants, variants_cursor)]
    sql = "SELECT Unabbreviated FROM ref_tool"
    if form.tool_include.choices is not None:
    	form.tool_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, variants, variants_cursor) if (b[0],b[0]) not in form.tool_include.choices]
    else:
    	form.tool_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, variants, variants_cursor)]

    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'records'"
    records = [b[0] for b in querySQL(sql, variants, variants_cursor)]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'samples'"
    samples = [b[0] for b in querySQL(sql, variants, variants_cursor)]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'genotype'"
    genotypes = [b[0] for b in querySQL(sql, variants, variants_cursor)]

    tools = [b[0].lower() for b in querySQL("SELECT tool FROM ref_tool", variants, variants_cursor)]
    tables = [b[0] for t in tools for b in querySQL("SELECT table_name from information_schema.tables where table_name like '%s_%%'" % (t), variants, variants_cursor)]
    tool_columns = {}
    tool_types = {}
    for t in tables:
    	table_cols = []
    	col_type = []
    	for b in querySQL("SELECT column_name from information_schema.columns where table_name = '%s'" % (t), variants, variants_cursor):
    		table_cols.append(b[0])
    	for d in querySQL("SELECT data_type from information_schema.columns where table_name = '%s'" % (t), variants, variants_cursor):
    		if "int" in d[0]:
    			col_type.append("num")
    		elif "float" in d[0]:
    			col_type.append("num")
    		elif "varchar" in d[0]:
    			col_type.append("str")
    		else:
    			col_type.append(d[0])
    	tool_columns.update({t:table_cols})
    	tool_types.update({t:col_type})
    return render_template('builder.html', form=form, cols=cols, tools=tools, tool_columns=tool_columns, tool_types=tool_types, records=records, samples=samples, genotypes=genotypes)