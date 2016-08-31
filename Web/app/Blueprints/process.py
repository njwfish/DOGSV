from flask import Blueprint, abort
from flask import render_template, redirect, request, url_for
from app.app import variants, variants_cursor, queries, queries_cursor
from app.forms import QueryForm
from app.MySQL_Utils import query_sql, insert_sql
from app.maps import Maps
from jinja2 import TemplateNotFound
from operator import itemgetter
from itertools import groupby

process = Blueprint('process', __name__, template_folder='templates')


def get_cluster(results, i, interval):
    cluster = []
    for j in range(i, 0, -1):
        if abs(results[i][2] - results[j][2]) < interval:
            cluster.append(results[j][0])
        else:
            break
    for j in range(i + 1, len(results)):
        if abs(results[i][2] - results[j][2]) < interval:
            cluster.append(results[j][0])
        else:
            break
    return cluster


def get_core_clusters(results):
    clusters = []
    for i in range(len(results) - 1):
        cluster = get_cluster(results, i, 100)
        if len(cluster) > 1:
            clusters.append(sorted(cluster))
    removed = 0
    for i in range(len(clusters)):
        i -= removed
        for j in range(len(clusters)):
            if not set(clusters[i]).issubset(set(clusters[j])) and i < j:
                break
            if set(clusters[i]).issubset(set(clusters[j])) and i != j:
                del clusters[i]
                removed += 1
                break
    return clusters


def cluster_results(query):
    ids = "select id, chrom, pos from" + query.lower().split('from')[1]
    results = query_sql(ids, variants, variants_cursor)
    results = sorted(results, key=lambda element: (element[1], element[2]))
    get_chrom = itemgetter(1)
    clusters = []
    for key, chrom in groupby(results, get_chrom):
        c = list(chrom)
        clusters = clusters + get_core_clusters(c)
    output = []
    for c in clusters:
        where = query.split('where')
        output.append([list(query_sql(where[0]
                                      + ('where id = %d and' % id)
                                      + where[1], variants, variants_cursor)[0]) for id in c])
    return output


@process.route('/process', methods=['GET', 'POST'])
def show():
    form = QueryForm()
    query = request.args['submit']
    clusters = []
    if query is not None and len(query) > 0:
        clusters = cluster_results(query)
        fields = [i[0].upper() for i in variants_cursor.description]
        print fields
        t = fields.index('TYPE') if 'TYPE' in fields else -1
        f = fields.index('FILTER') if 'FILTER' in fields else -1
        g = fields.index('GT') if 'GT' in fields else -1
        s = fields.index('SAMPLE_ID') if 'SAMPLE_ID' in fields else -1
        id_map = Maps(variants, variants_cursor, 0)
        id_map.gen_dicts()
        for c in clusters:
            for i in range(len(c)):
                if t > -1:
                    c[i][t] = id_map.variant_mapping[c[i][t]] \
                        if c[i][t] in id_map.variant_mapping else 'None'
                if f > -1:
                    c[i][f] = id_map.filter_mapping[c[i][f]] \
                        if c[i][f] in id_map.filter_mapping else 'None'
                if g > -1:
                    c[i][g] = id_map.genotype_mapping[c[i][g]] \
                        if c[i][g] in id_map.genotype_mapping else 'None'
                if s > -1:
                    c[i][s] = id_map.sample_mapping[c[i][s]] \
                        if c[i][s] in id_map.sample_mapping else 'None'
        insert_sql("queries ", ["query"], [query], queries, queries_cursor)

    try:
        return render_template('process.html', form=form, fields=fields, clusters=clusters, query=query)
    except TemplateNotFound:
        abort(404)

