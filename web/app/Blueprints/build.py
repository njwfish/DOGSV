import ast
from flask import redirect, request, url_for
from collections import defaultdict
from flask import Blueprint, abort
from jinja2 import TemplateNotFound
from app.app import maps

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
    types = ["type = '%s'" % (maps.variant_mapping[type_keys[i]]) for i in range(len(type_vals)) if type_vals[i]]
    gt_vals = genotypes.values()
    gt_keys = genotypes.keys()
    genotypes = ["g.gt = '%s'" % (maps.genotype_mapping[gt_keys[i]]) for i in range(len(gt_vals)) if gt_vals[i] == 1]
    samples = ["g.sample_id = '%s'" % (maps.sample_mapping[sample]) for sample in samples]
    breeds = ["breed_type = '%s'" % (maps.breed_mapping[breed]) for breed in breeds]
    tools = ["t.tool = '%s'" % (maps.tool_mapping[maps.tool_name_mapping[tool]]) for tool in tools]
    regions = ["(%s)" % region.replace(" is ", "=") for region in regions]
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

    if "r" in necessary_joins:
        necessary_joins.remove("r")
    '''TODO: distill necessary joins to just the list, with no ancillary checks'''

    if len(samples) > 0 or len(genotypes) > 0 or "g" in necessary_joins or "s" in necessary_joins:
        g = 'INNER JOIN genotype g on g.record_id=r.id '
        if len(samples) > 0:
            g = '%s and (%s) ' % (g, ' or '.join(samples))
        if len(genotypes) > 0:
            g = '%s and (%s)' % (g, ' or '.join(genotypes))
        query.append(g)
        if "g" in necessary_joins:
            necessary_joins.remove("g")

    if len(breeds) > 0 or "s" in necessary_joins:
        s = 'INNER JOIN samples s on s.sample_id=g.sample_id '
        if len(breeds) > 0:
            s = '%sand individual_id in (select individual_id from individuals where %s)' % (s, ' or '.join(breeds))
        query.append(s)
        necessary_joins.remove("s")

    if len(tools) > 0:
        query.append('INNER JOIN tools_used t on t.record_id=r.id and %s' % (' or '.join(tools)))

    if len(necessary_joins) > 0:
        for j in necessary_joins:
            f = 'INNER JOIN %s on %s.record_id=r.id ' % (j, j)
            if len(filters.keys()) > 0:
                f = '%s and (%s)' % (f, ' and '.join(filters[j]))
            query.append(f)

    core = []
    if len(filters['r']) > 0:
        core.append(' and '.join(filters['r']))
    if len(types) > 0:
        core.append('(%s)' % ' or '.join(types))
    if len(regions) > 0:
        core.append('(%s)' % ' or '.join(regions))
    if len(core) > 0:
        query.append('where %s' % ' and '.join(core))

    cols = []
    if len(columns) > 0:
        cols.append(', '.join(columns))
    if len(cols) == 0:
        cols = ['chrom,pos,filter,type,chrom2,pos2,len']

    query = "select %s from records r %s limit 5000" % (', '.join(cols), ' '.join(query))
    try:
        return redirect(url_for('results.show', query=query))
    except TemplateNotFound:
        abort(404)