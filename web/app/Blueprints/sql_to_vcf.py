from flask import request, send_from_directory
from VCFQuery import VCFQuery
from web.app.app import queries_cursor
from flask import Blueprint, abort
from jinja2 import TemplateNotFound

sql_to_vcf = Blueprint('sql_to_vcf', __name__, template_folder='templates')


@sql_to_vcf.route('/sql_to_vcf/', methods=['GET', 'POST'])
def show():
    vcf = VCFQuery(request.args['submit'], str(queries_cursor.lastrowid), 1, 0)
    download = vcf.sql_to_vcf()
    try:
        return send_from_directory('static', download, attachment_filename=download)
    except TemplateNotFound:
        abort(404)
