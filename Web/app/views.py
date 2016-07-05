from flask import render_template, flash, redirect, request
from app import app, cursor
from .forms import RecordForm
from MySQL_Utils import executeSQL, querySQL, insertSQL

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',title='Home')

@app.route('/results')
def results():
    return render_template('results.html', results=results)

@app.route('/builder', methods=['GET', 'POST'])
def builder():
    sql = "SELECT Unabbreviated FROM ref_breed"
    AVAILABLE_BREEDS = querySQL(sql, cursor)
    DEFAULT_CHOICES = []
    form = RecordForm()
    breeds = []
    form.breed_exclude.choices = [(b[0],b[0]) for b in AVAILABLE_BREEDS]
    
    if request.method == 'POST':
        form.breed_include.choices = AVAILABLE_BREEDS
        if form.validate_on_submit():
            flash('Select * from records where chrom=%s and pos=%s' % (str(form.chrom.data), str(form.pos.data)))
            return redirect('/index')
        else:
            form.breed_include.choices = DEFAULT_CHOICES

    return render_template('builder.html', form=form)