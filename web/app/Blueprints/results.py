from flask import Blueprint, abort
from flask import render_template, redirect, request, url_for, session, jsonify
from app.app import variants, variants_cursor, queries, queries_cursor
from app.forms import QueryForm
from app.MySQL_Utils import query_sql, insert_sql
from app.query import Query
from jinja2 import TemplateNotFound

results = Blueprint('results', __name__, template_folder='templates')


@results.route('/results/', methods=['GET', 'POST'])
def show():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results.show', query=form.input_query.data))
    query = request.args['query']
    try:
        session['query'] = Query(query, interval=100)
    except KeyError:
        session['query'] = 1
    print session['query']
    results = session['query'].get_results()
    fields = session['query'].get_fields()
    if results is not None and len(results) > 0:
        insert_sql("queries ", ["query"], [query], queries, queries_cursor)
        results = sorted(results, key=lambda element: (element[0], element[1]))
    try:
        return render_template('results.html', form=form, fields=fields, results=results, query=query)
    except TemplateNotFound:
        abort(404)
