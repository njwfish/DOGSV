from flask import render_template, flash, redirect, request, url_for
from app import app, cursor
from .forms import RecordForm
from MySQL_Utils import executeSQL, querySQL, insertSQL

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',title='Home')

@app.route('/results/<records><types><genotypes><samples><breeds><tools>')
def results(records, types, genotypes, samples, breeds, tools):
    print records
    sql = "select * from records where ()"
    return render_template('results.html')

@app.route('/builder', methods=['GET', 'POST'])
def builder():
    form = RecordForm()
    if request.method == 'POST':
        form.breed_include.choices = [(str(b), str(b)) for b in form.breed_include.data] 
        form.sample_include.choices = [(str(b), str(b)) for b in form.sample_include.data] 
        form.tool_include.choices = [(str(b), str(b)) for b in form.tool_include.data] 
        if form.validate_on_submit():
            records = {
            'chrom':form.chrom.data, 
            'chrom2':form.chrom2.data, 
            'filt':form.filt.data, 
            'pos':form.pos.data,
            'pos2':form.pos2.data,
            'length':form.length.data, 
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
            samples = {
            'samples':form.sample_include.data, 
            'tumor':form.tumor.data, 
            }
            breeds = form.breed_include.data,
            tools = form.tool_include.data 
            return redirect(url_for('results', records=records, types=types, genotypes=genotypes, samples=samples, breeds=breeds, tools=tools))
    sql = "SELECT Unabbreviated FROM ref_breed"
    form.breed_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, cursor) if (b[0],b[0]) not in form.breed_include.choices]
    sql = "SELECT sample_id FROM samples"
    form.sample_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, cursor) if (b[0],b[0]) not in form.sample_include.choices]
    sql = "SELECT Unabbreviated FROM ref_tool"
    form.tool_exclude.choices = [(b[0],b[0]) for b in querySQL(sql, cursor) if (b[0],b[0]) not in form.tool_include.choices]
    return render_template('builder.html', form=form)