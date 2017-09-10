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
        #TODO: use the dissassembler to parse this out...
        return redirect(url_for('results.show', query=form.input_query.data))
    table = 'records'
    columns = request.args['columns']
    joins = request.args['joins'].split('|') if 'joins' in request.args else []
    print "JOINS", joins
    requirements = request.args['requirements'] if 'requirements' in request.args else ''
    try:
        if session['query'].requirements != requirements:
            session['query'] = Query(columns, table, joins, requirements)
        elif session['query'].columns != columns:
            session['query'].columns = columns
            session['query'].joins = joins
    except AttributeError:
        # Change to route to query error page
        abort(404)
    except KeyError:
        session['query'] = Query(columns, table, joins, requirements)
    rows, fields = session['query'].get_results()
    if results is not None and len(rows) > 0:
        insert_sql("queries ", ["query"], [session['query'].get_sql()], queries, queries_cursor)
        if len(fields) > 2:
            rows = sorted(rows, key=lambda element: (element[0], element[1]))
    try:
        return render_template('results.html', form=form, fields=fields, results=rows, query=session['query'].get_sql())
    except TemplateNotFound:
        abort(404)
