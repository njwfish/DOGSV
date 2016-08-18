from flask import Blueprint, abort, render_template
from app.app import queries, queries_cursor
from app.MySQL_Utils import query_sql
from jinja2 import TemplateNotFound


library = Blueprint('library', __name__, template_folder='templates')


@library.route('/library', methods=['GET', 'POST'])
def show():
    results = query_sql("select time, query from queries", queries, queries_cursor)
    results = [[v for v in r] for r in results] if results is not None else results
    fields = [i[0] for i in queries_cursor.description]
    try:
        return render_template('library.html', fields=fields, results=results)
    except TemplateNotFound:
        abort(404)
