from flask import Blueprint, abort
from flask import render_template, redirect, request, url_for, session
from web.app.app import variants, variants_cursor, queries, queries_cursor
from web.app.forms import QueryForm
from MySQL_Utils import query_sql, insert_sql
from Query import Query, QueryParser
from jinja2 import TemplateNotFound

results = Blueprint('results', __name__, template_folder='templates')


@results.route('/results/', methods=['GET', 'POST'])
def show():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results.show', query=form.input_query.data))
    query = request.args['query']
    print "results"
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
    rows, fields = session['query'].get_results()
    if results is not None and len(rows) > 0:
        insert_sql("queries ", ["query"], [query], queries, queries_cursor)
        if len(fields) > 2:
            rows = sorted(rows, key=lambda element: (element[0], element[1]))
    try:
        return render_template('results.html', form=form, fields=fields, results=rows, query=query)
    except TemplateNotFound:
        abort(404)
