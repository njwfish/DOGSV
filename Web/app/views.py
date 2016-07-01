from flask import render_template, flash, redirect
from app import app
from .forms import RecordForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',title='Home')

@app.route('/results')
def results():
    return render_template('results.html', results=results)

@app.route('/builder', methods=['GET', 'POST'])
def builder():
    form = RecordForm()
    if form.validate_on_submit():
        flash('Select * from records where chrom=%s and pos=%s' % (str(form.chrom.data), str(form.pos.data)))
        return redirect('/index')
    return render_template('builder.html', title='Builder', form=form)