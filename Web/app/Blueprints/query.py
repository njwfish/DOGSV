from app.forms import QueryForm
from flask import redirect, request, url_for

from flask import Blueprint, abort, render_template
from jinja2 import TemplateNotFound


query = Blueprint('query', __name__, template_folder='templates')


@query.route('/query', methods=['GET', 'POST'])
def show():
    form = QueryForm()
    if request.method == 'POST':
        return redirect(url_for('results.show', query=form.input_query.data))
    try:
        return render_template('query.html', form=form)
    except TemplateNotFound:
        abort(404)
