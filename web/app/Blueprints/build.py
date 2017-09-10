import ast
from flask import redirect, request, url_for
from collections import defaultdict
from flask import Blueprint, abort
from jinja2 import TemplateNotFound
from web.app.app import maps

build = Blueprint('build', __name__, template_folder='templates')


@build.route('/build/')
def show():
    query = []
    types = ast.literal_eval(request.args['types'])
    genotypes = ast.literal_eval(request.args['genotypes'])
    tumor = request.args['tumor'] if request.args['tumor'] == 'True' else ''
    samples = ast.literal_eval(request.args['samples'])
    breeds = ast.literal_eval(request.args['breeds'])
    tools = ast.literal_eval(request.args['tools'])
    tool_filters = ast.literal_eval(request.args['tool_filters'])
    columns = ast.literal_eval(request.args['columns'])
    regions = ast.literal_eval(request.args['regions'])
    type_vals = types.values()
    type_keys = types.keys()
    types = ["records.type = '%s'" % (maps.variant_mapping[type_keys[i]]) for i in range(len(type_vals)) if type_vals[i]]
    gt_vals = genotypes.values()
    gt_keys = genotypes.keys()
    genotypes = ["genotype.gt = '%s'" % (maps.genotype_mapping[gt_keys[i]]) for i in range(len(gt_vals)) if gt_vals[i] == 1]
    samples = ["genotype.sample_id = '%s'" % (maps.sample_mapping[sample]) for sample in samples]
    breeds = ["breed_type = '%s'" % (maps.breed_mapping[breed]) for breed in breeds]
    tools = ["tools_used.tool = '%s'" % (maps.tool_mapping[maps.tool_name_mapping[tool]]) for tool in tools]
    regions = ["%s" % region.replace(" is ", "=") for region in regions]
    necessary_joins = []


    filters = defaultdict(list)
    for f in tool_filters:
        table = f.split(".")[0]
        filters[table].append(f.split(".")[1])
        if table not in necessary_joins:
            necessary_joins.append(table)
    for c in columns:
        table = c.split(".")[0]
        if table not in necessary_joins:
            necessary_joins.append(table)

    if "records" in necessary_joins:
        necessary_joins.remove("records")
    '''TODO: distill necessary joins to just the list, with no ancillary checks'''

    requirements = []
    joins = []

    if len(samples) > 0 or len(genotypes) > 0 or "genotype" in necessary_joins or "samples" in necessary_joins:
        joins.append('INNER JOIN genotype on genotype.record_id=records.id')
        if len(samples) > 0:
            requirements.append(' or '.join(samples))
        if len(genotypes) > 0:
            requirements.append(' or '.join(genotypes))
        if "genotype" in necessary_joins:
            necessary_joins.remove("genotype")

    if len(breeds) > 0 or "samples" in necessary_joins:
        joins.append('INNER JOIN samples on samples.sample_id=genotype.sample_id')
        if "samples" in necessary_joins:
            necessary_joins.remove("samples")

    if len(breeds) > 0:
        joins.append('INNER JOIN individuals on individuals.individual_id=sample.individual_id')
        requirements.append(' or '.join(breeds))
        if "individuals" in necessary_joins:
            necessary_joins.remove("individuals")

    if len(tools) > 0:
        joins.append('INNER JOIN tools_used on tools_used.record_id=records.id')
        requirements.append(' or '.join(tools))

    if len(necessary_joins) > 0:
        for j in necessary_joins:
            joins.append('INNER JOIN %s on %s.record_id=records.id ' % (j, j))

    for key in filters.keys():
        requirements.append(filters[key])

    regoins = ['(' + ' or '.join(regions) + ')'] if len(regions) > 0 else []
    types = ['(' + ' or '.join(types) + ')'] if len(types) > 0 else []
    requirements += regions + types
    requirements = '(' + ') and ('.join(requirements) + ')' if len(requirements) > 0 else ''

    cols = ''
    if len(columns) > 0:
        cols = ', '.join(columns)
    if cols == '':
        cols = 'records.chrom,records.pos,records.filter,records.type,records.chrom2,records.pos2,records.len'


    query = "select %s from records %s" % (', '.join(cols), ' '.join(query))
    print "BUILDER", cols, joins, requirements
    try:
        return redirect(url_for('results.show', columns=cols, joins='|'.join(joins), requirements=requirements))
    except TemplateNotFound:
        abort(404)