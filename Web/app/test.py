from MySQL_Utils import query_sql, insert_sql
from maps import Maps
import MySQLdb
import sys

variants = MySQLdb.connect("localhost", "root", "12345", "DogSVStore")
variants_cursor = variants.cursor()
maps = Maps(variants, variants_cursor, 1)
maps.gen_dicts()


def get_cluster(results, i, dist, interval, dir, cluster):
    j = i + dir * dist
    if 0 < j < len(results):
        if abs(results[i][1] - results[j][1]) < interval:
            cluster.append(j)
        else:
            return cluster
    return get_cluster(results, i, dist - ((dir - 1) / 2), interval, -dir, cluster)

sys.setrecursionlimit(10000)
results = query_sql("select chrom, pos from records where chrom=1 and pos between 0 and 36079;", variants, variants_cursor)
results = [list(r) for r in results] if results is not None else results
results = sorted(results, key=lambda element: (element[0], element[1]))
clusters = []
for i in range(len(results)):
    cluster = get_cluster(results, i, 1, 50, 1, [i])
    if len(cluster) > 1:
        clusters.append(sorted(cluster))
removed = 0
for i in range(len(clusters)):
    i -= removed
    for j in range(len(clusters)):
        if set(clusters[i]).issubset(set(clusters[j])) and i != j:
            del clusters[i]
            removed += 1
            break
print clusters
