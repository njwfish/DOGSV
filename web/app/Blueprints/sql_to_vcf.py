from flask import request, send_from_directory
from flask import request, session
from VCFQuery import VCFQuery
from web.app.app import queries_cursor
from flask import Blueprint, abort
from jinja2 import TemplateNotFound
import os
from Query import Query, QueryParser

sql_to_vcf = Blueprint('sql_to_vcf', __name__, template_folder='templates')


@sql_to_vcf.route('/sql_to_vcf/', methods=['GET', 'POST'])
def show():
    print "TEST"

    query = session['query']

    tmp_dir = os.path.dirname(os.path.dirname(__file__)) + '/tmp/'

    vcf = VCFQuery(query, tmp_dir, str(queries_cursor.lastrowid), 1, 0)
    download = vcf.sql_to_vcf()
    print "SUCCESS"
    try:
        return send_from_directory('tmp', download, attachment_filename=download)
    except TemplateNotFound:
        abort(404)
