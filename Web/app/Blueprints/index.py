from flask import Blueprint, abort, render_template
from app.forms import SearchForm
from jinja2 import TemplateNotFound


index = Blueprint('index', __name__, template_folder='templates')


@index.route('/')
@index.route('/index')
def show():
    form = SearchForm()
    try:
        return render_template('search.html', form=form)
    except TemplateNotFound:
        abort(404)

