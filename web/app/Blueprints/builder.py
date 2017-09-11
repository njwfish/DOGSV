from web.app.app import variants, variants_cursor
from flask import redirect, request, url_for
from web.app.forms import BuilderForm, ColumnForm
from MySQL_Utils import query_sql

from flask import Blueprint, abort, render_template
from jinja2 import TemplateNotFound


builder = Blueprint('builder', __name__, template_folder='templates')

@builder.route('/')
@builder.route('/builder', methods=['GET', 'POST'])
def show():
    form = BuilderForm(prefix="form")
    cols = ColumnForm(prefix="cols")
    if request.method == 'POST':
        form.breed_include.choices = [(str(b), str(b)) for b in form.breed_include.data]
        form.sample_include.choices = [(str(b), str(b)) for b in form.sample_include.data]
        form.tool_include.choices = [(str(b), str(b)) for b in form.tool_include.data]
        form.region_include.choices = [(str(b), str(b)) for b in form.region_include.data]
        form.breed_exclude.choices = [(str(b), str(b)) for b in form.breed_exclude.data]
        form.sample_exclude.choices = [(str(b), str(b)) for b in form.sample_exclude.data]
        form.tool_exclude.choices = [(str(b), str(b)) for b in form.tool_exclude.data]
        form.region_exclude.choices = [(str(b), str(b)) for b in form.region_exclude.data]
        form.tool_clauses.choices = [(str(b),str(b)) for b in form.tool_clauses.data]

        cols.columns_include.choices = [(str(b), str(b)) for b in cols.columns_include.data]
        cols.columns_exclude.choices = [(str(b), str(b)) for b in cols.columns_exclude.data]
        if form.validate_on_submit():
            types = {
                'DEL': form.DEL.data,
                'DUP': form.DUP.data,
                'INS': form.INS.data,
                'INV': form.INV.data,
                'TRA': form.TRA.data,
                'SIN': form.SIN.data,
                'LIN': form.LIN.data,
                'BXP': form.BXP.data
            }
            genotypes_cols = {
                '0/0': form.homref.data,
                '0/1': form.het.data,
                '1/1': form.homalt.data
            }
            regions = form.region_include.data,
            tumor = form.tumor.data
            samples_cols = form.sample_include.data,
            breeds = form.breed_include.data,     # adding a comma here avoids a bad request
            tools = form.tool_include.data,       # adding a comma here avoids a bad request
            tool_filters = '["' + '", "'.join(form.tool_clauses.data) + '"]' \
                if len(form.tool_clauses.data) > 0 else '[]'
            columns = cols.columns_include.data,
            return redirect(url_for('build.show', types=types, genotypes=genotypes_cols,
                                    regions=regions, tumor=tumor, samples=samples_cols,
                                    breeds=breeds, tools=tools, tool_filters=tool_filters, columns=columns))

    sql = "SELECT Unabbreviated FROM ref_breed"
    if form.breed_include.choices is not None and len(form.breed_include.choices) > 0:
        form.breed_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)
                                      if (b[0], b[0]) not in form.breed_include.choices]
    else:
        form.breed_exclude.choices = [(b[0],b[0]) for b in query_sql(sql, variants, variants_cursor)]
    sql = "SELECT Unabbreviated FROM ref_tool"
    if form.tool_include.choices is not None:
        form.tool_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)
                                     if (b[0], b[0]) not in form.tool_include.choices]
    else:
        form.tool_exclude.choices = [(b[0], b[0]) for b in query_sql(sql, variants, variants_cursor)]

    sql = "SELECT sample FROM ref_sample"
    sample_options = [(b[0],b[0]) for b in query_sql(sql, variants, variants_cursor)]

    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'records'"
    results = query_sql(sql, variants, variants_cursor)
    records_cols = [b[0] for b in results] if results is not None else []
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'samples'"
    results = query_sql(sql, variants, variants_cursor)
    samples_cols = [b[0] for b in results] if results is not None else []
    sql = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'genotype'"
    results = query_sql(sql, variants, variants_cursor)
    genotypes_cols = [b[0] for b in results] if results is not None else []

    sql = "SELECT tool FROM ref_tool"
    tools = [b[0].lower() for b in query_sql(sql, variants, variants_cursor)]
    tables = [b[0] for t in tools for b in
              query_sql("SELECT table_name from information_schema.tables where table_name like '%s_%%'" % t,
                        variants, variants_cursor)]
    tool_columns = {}
    tool_types = {}
    for t in tables:
        table_cols = []
        col_type = []
        sql = "SELECT column_name from information_schema.columns where table_name = '%s'" % t
        for b in query_sql(sql, variants, variants_cursor):
            table_cols.append(b[0])
        sql = "SELECT data_type from information_schema.columns where table_name = '%s'" % t
        for d in query_sql(sql, variants, variants_cursor):
            if "int" in d[0]:
                col_type.append("num")
            elif "float" in d[0]:
                col_type.append("num")
            elif "varchar" in d[0]:
                col_type.append("str")
            else:
                col_type.append(d[0])
        tool_columns.update({t: table_cols})
        tool_types.update({t: col_type})

    try:
        return render_template('builder.html', form=form, cols=cols, tools=tools,
                               tool_columns=tool_columns, tool_types=tool_types, records=records_cols,
                               samples=samples_cols, genotypes=genotypes_cols, sample_options=sample_options)
    except TemplateNotFound:
        abort(404)