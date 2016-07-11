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
    results = querySQL(request.args['query'], db, cursor)
    fields = [i[0] for i in cursor.description]
    return render_template('results.html', fields = fields, results=results)

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
    if len(recCols) < 1:
    	recCols = ['*']
    samCols = ast.literal_eval(request.args['samCols'])
    gtpCols = ast.literal_eval(request.args['gtpCols'])
    recVals = records.values()
    recKeys = records.keys()
    records = ["%s = '%s'" % (recKeys[i], recVals[i]) for i in range(len(recVals)) if recVals[i] is not None and len(str(recVals[i])) > 0]
    typeVals = types.values()
    typeKeys = types.keys()
    types = ["type = '%s'" % (maps.variant_mapping[typeKeys[i]]) for i in range(len(typeVals)) if typeVals[i]]
    records.append('(%s)' % ' or '.join(types))
    gtVals = genotypes.values()
    gtKeys = genotypes.keys()
    genotypes = ["%s = '%s'" % (gtKeys[i], gtVals[i]) for i in range(len(gtVals)) if gtVals[i] == 1]
    samples = ["sample_id = '%s'" % (maps.sample_mapping[sample]) for sample in samples]
    breeds = ["breed_id = '%s'" % (maps.breed_mapping[breed]) for breed in breeds]
    tools = ["tool = '%s'" % (maps.tool_mapping[maps.tool_name_mapping[tool]]) for tool in tools]
    if len(samples) > 0:
        query.append('(%s)' % ' or '.join(samples))
    if len(breeds) > 0:
        query.append('individual_id in (select individual_id from individuals where %s)' % ' or '.join(breeds))
    if len(query) > 0:
        query = ['id in (select record_id from genotypes where sample_id in (select sample_id from samples where %s)' % (' or '.join(query))]
    if len(tools) > 0:
        query.append('id in (select record_id from tools_used where %s)' % (' or '.join(tools)))
    if len(query) > 0:
        query = ['(%s)' ' or '.join(query)]
    if len(records) > 0:
        query.append(' and '.join(records))
    if len(query) > 0:
        query = "where %s " % (' and '.join(query))
    else:
        query = ''
    query = "select %s from records %s" % (', '.join(recCols), query)
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
        form.breed_exclude.choices = [(str(b), str(b)) for b in form.breed_exclude.data] 
        form.sample_exclude.choices = [(str(b), str(b)) for b in form.sample_exclude.data] 
        form.tool_exclude.choices = [(str(b), str(b)) for b in form.tool_exclude.data]

        cols.records_include.choices = [(str(b), str(b)) for b in cols.records_include.data]
        cols.records_exclude.choices = [(str(b), str(b)) for b in cols.records_exclude.data]
        cols.samples_include.choices = [(str(b), str(b)) for b in cols.samples_include.data]
        cols.samples_exclude.choices = [(str(b), str(b)) for b in cols.samples_exclude.data]
        cols.genotypes_include.choices = [(str(b), str(b)) for b in cols.genotypes_include.data]
        cols.genotypes_exclude.choices = [(str(b), str(b)) for b in cols.genotypes_exclude.data]


        if cols.validate_on_submit():
            print "test"
        if form.validate_on_submit():
            records = {
            'chrom':form.chrom.data, 
            'chrom2':form.chrom2.data, 
            'filter':form.filter.data, 
            'pos':form.pos.data,
            'pos2':form.pos2.data,
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
            'homref':form.homref.data, 
            'het':form.het.data, 
            'homalt':form.homalt.data
            }
            tumor = form.tumor.data
            samples = form.sample_include.data, 
            breeds = form.breed_include.data,     #adding a comma here avoids a bad request
            tools = form.tool_include.data,        #adding a comma here avoids a bad request
            recCols = cols.records_include.data,
            samCols = cols.samples_include.data,
            gtpCols = cols.genotypes_include.data,
            return redirect(url_for('build', records=records, types=types, genotypes=genotypes, tumor=tumor, samples=samples, breeds=breeds, tools=tools, recCols=recCols, samCols=samCols, gtpCols=gtpCols))

    sql = "SELECT Unabbreviated FROM ref_breed"
    form.breed_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if form.breed_include.choices is not None and (b[0],b[0]) not in form.breed_include.choices]
    sql = "SELECT sample_id FROM samples"
    form.sample_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if form.sample_include.choices is not None and (b[0],b[0]) not in form.sample_include.choices]
    sql = "SELECT Unabbreviated FROM ref_tool"
    form.tool_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if form.tool_include.choices is not None and (b[0],b[0]) not in form.tool_include.choices]

    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = N'Records'"
    cols.records_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if cols.records_include.choices is not None and (b[0],b[0]) not in cols.records_include.choices]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = N'samples'"
    cols.samples_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if cols.samples_include.choices is not None and (b[0],b[0]) not in cols.samples_include.choices]
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = N'genotypes'"
    cols.genotypes_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, db, cursor) if cols.genotypes_include.choices is not None and (b[0],b[0]) not in cols.genotypes_include.choices]

    return render_template('builder.html', form=form, cols=cols)















