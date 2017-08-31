from flask import Blueprint, abort
from flask import render_template, redirect, request, url_for,  session
from web.app.forms import QueryForm
from jinja2 import TemplateNotFound
from Query import Query, QueryParser


process = Blueprint('processing', __name__, template_folder='templates')

@process.route('/processing', methods=['GET', 'POST'])
def show():
    print "processing"
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results.show', query=form.input_query.data))
    query = request.args['submit']
    try:
        columns, table, joins, requirements, order = QueryParser.parse(query)
    except AttributeError:
        # Change to route to query error page
        abort(404)
    try:
        if session['query'].table != table or session['query'].requirements != requirements:
            session['query'] = Query(columns, table, joins, requirements)
        elif session['query'].columns != columns:
            session['query'].columns = columns
            session['query'].joins = joins
    except KeyError:
        session['query'] = Query(columns, table, joins, requirements, order)
    if session['submit'].clusters is None:
        session['submit'].cluster_results()
    results, fields = session['submit'].get_clustered_results()
    try:
        return render_template('processing.html', form=form, fields=fields, clusters=results, query=query)
    except TemplateNotFound:
        abort(404)

