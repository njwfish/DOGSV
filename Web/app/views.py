import ast
from flask import render_template, flash, redirect, request, url_for
from app import app, db, cursor, maps
from .forms import BuilderForm, QueryForm, SearchForm, ColumnForm
from MySQL_Utils import executeSQL, querySQL, insertSQL

@app.route('/')
@app.route('/index')
def index():
    form = SearchForm()
    return render_template('search.html', form=form)

@app.route('/results/')
def results():
    query = request.args['query']
    results = querySQL(query, db, cursor)
    fields = [i[0] for i in cursor.description]
    results = sorted(results, key=lambda element: (element[0], element[1]))
    return render_template('results.html', fields = fields, results=results, query=query)

@app.route('/query', methods=['GET', 'POST'])
def query():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results', query=form.query.data))
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
    recCols = ast.literal_eval(request.args['recCols']) 
    samCols = ast.literal_eval(request.args['samCols'])
    gtpCols = ast.literal_eval(request.args['gtpCols'])
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


    if len(gtpCols) > 0 or len(samples) > 0 or len(genotypes) > 0:
    	g = 'INNER JOIN genotype g on g.record_id=r.id '
    	if len(samples) > 0:
        	g = '%s and (%s) ' % (g, ' or '.join(samples))
    	if len(genotypes) > 0:
        	g = '%s and (%s)' % (g, ' or '.join(genotypes))
        query.append(g)

    if len(breeds) > 0 or len(samCols) > 0:
        s = 'INNER JOIN samples s on s.sample_id=g.sample_id '
        if len(breeds) > 0:
            s = '%sand individual_id in (select individual_id from individuals where %s)' % (s, ' or '.join(breeds))
        query.append(s)

    if len(tools) > 0:
        query.append('INNER JOIN tools_used t on t.record_id=r.id and %s' % (' or '.join(tools)))

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
    if len(recCols) > 0:
    	cols.append(', '.join(recCols))
    if len(samCols) > 0:
    	cols.append('s.%s' % ', s.'.join(samCols))
    if len(gtpCols) > 0:
    	cols.append('g.%s' % ', g.'.join(gtpCols))
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

        cols.records_include.choices = [(str(b), str(b)) for b in cols.records_include.data]
        cols.records_exclude.choices = [(str(b), str(b)) for b in cols.records_exclude.data]
        cols.samples_include.choices = [(str(b), str(b)) for b in cols.samples_include.data]
        cols.samples_exclude.choices = [(str(b), str(b)) for b in cols.samples_exclude.data]
        cols.genotypes_include.choices = [(str(b), str(b)) for b in cols.genotypes_include.data]
        cols.genotypes_exclude.choices = [(str(b), str(b)) for b in cols.genotypes_exclude.data]
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
            recCols = cols.records_include.data,
            samCols = cols.samples_include.data,
            gtpCols = cols.genotypes_include.data,
            return redirect(url_for('build', records=records, types=types, genotypes=genotypes, regions=regions, tumor=tumor, samples=samples, breeds=breeds, tools=tools, recCols=recCols, samCols=samCols, gtpCols=gtpCols))

    sql = "SELECT Unabbreviated FROM ref_breed"
    if form.breed_include.choices is not None:
    	form.breed_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if (b[0],b[0]) not in form.breed_include.choices]
    else:
    	form.breed_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor)]
    sql = "SELECT sample FROM ref_sample"
    if form.sample_include.choices is not None:
    	form.sample_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if (b[0],b[0]) not in form.sample_include.choices]
    else:
    	form.sample_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor)]
    sql = "SELECT Unabbreviated FROM ref_tool"
    if form.tool_include.choices is not None:
    	form.tool_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if (b[0],b[0]) not in form.tool_include.choices]
    else:
    	form.tool_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor)]

    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = N'Records'"
    if cols.records_include.choices is not None:
    	cols.records_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if (b[0],b[0]) not in cols.records_include.choices]
    else:
    	cols.records_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor)]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = N'samples'"
    if cols.samples_include.choices is not None:
    	cols.samples_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if (b[0],b[0]) not in cols.samples_include.choices]
    else:
    	cols.samples_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor)]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = N'genotype'"
    if cols.genotypes_include.choices is not None:
    	cols.genotypes_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if (b[0],b[0]) not in cols.genotypes_include.choices]
    else:
    	cols.genotypes_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor)]

    return render_template('builder.html', form=form, cols=cols)