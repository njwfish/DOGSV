from flask import Blueprint, abort
from flask import render_template, redirect, request, url_for
from app.app import variants, variants_cursor, queries, queries_cursor
from app.forms import QueryForm
from app.MySQL_Utils import query_sql, insert_sql
from app.maps import Maps
from jinja2 import TemplateNotFound

process = Blueprint('process', __name__, template_folder='templates')


def get_cluster(results, i, dist, interval, dir, cluster):
    j = i + dir * dist
    print i, j
    if 0 < j < len(results):
        print results[i][1] - results[j][1]
        if results[i][1] - results[j][1] < interval:
            cluster.append(j)
        else:
            return cluster
    return get_cluster(results, i, dist + (dir - 1) / 2, interval, -dir, cluster)

@process.route('/process', methods=['GET', 'POST'])
def show():
    print request.args
    query = request.args['submit']
    results = query_sql(query, variants, variants_cursor)
    results = [list(r) for r in results] if results is not None else results
    fields = [i[0] for i in variants_cursor.description]
    if results is not None and len(results) > 0:
        t = fields.index('TYPE') if 'TYPE' in fields else -1
        f = fields.index('FILTER') if 'FILTER' in fields else -1
        g = fields.index('GT') if 'GT' in fields else -1
        s = fields.index('sample_id') if 'sample_id' in fields else -1
        id_map = Maps(variants, variants_cursor, 0)
        id_map.gen_dicts()
        results = sorted(results, key=lambda element: (element[0], element[1]))
        clusters = []
        for i in range(len(results)):
            cluster = get_cluster(results, i, 1, 50, 1, [])
            if len(cluster) > 1:
                clusters.append(cluster)
            print clusters
            if t > -1:
                results[i][t] = id_map.variant_mapping[results[i][t]] if results[i][
                                                                             t] in id_map.variant_mapping else 'None'
            if f > -1:
                results[i][f] = id_map.filter_mapping[results[i][f]] if results[i][
                                                                            f] in id_map.filter_mapping else 'None'
            if g > -1:
                results[i][g] = id_map.genotype_mapping[results[i][g]] if results[i][
                                                                              g] in id_map.genotype_mapping else 'None'
            if s > -1:
                results[i][s] = id_map.sample_mapping[results[i][s]] if results[i][
                                                                            s] in id_map.sample_mapping else 'None'
        insert_sql("queries ", ["query"], [query], queries, queries_cursor)

    try:
        return url_for('results.show', query=query)
    except TemplateNotFound:
        abort(404)

