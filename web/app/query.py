from maps import Maps
import MySQLdb
from operator import itemgetter
from itertools import groupby
from uuid import uuid4
from MySQL_Utils import query_sql, execute_sql
from flask.json import JSONEncoder, JSONDecoder


class QueryJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Query):
            query_dict = {'query': obj.query,
                          'tid': obj.tid,
                          'clusters': obj.clusters,
                          'interval': obj.interval}
            return query_dict
        else:
            JSONEncoder.default(self, obj)


class QueryJSONDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        self.orig_obj_hook = kwargs.pop("object_hook", None)
        super(QueryJSONDecoder, self).__init__(*args, object_hook=self.query_obj_hook, **kwargs)

    def query_obj_hook(self, d):
        # Calling custom decode function:
        print d
        if 'query' in d:
            return self.decode_query(d)
        if self.orig_obj_hook:  # Do we have another hook to call?
            return self.orig_obj_hook(d)  # Yes: then do it
        return d  # No: just return the decoded dict

    @staticmethod
    def decode_query(d):
        query = Query(d['query'], tid=d['tid'], clusters=d['clusters'], interval=d['interval'])
        return query


class Query:
    def __init__(self, query, tid=None, clusters=None, interval=None):
        self.variants = MySQLdb.connect("localhost", "root", "12345", "DogSVStore")
        self.variants_cursor = self.variants.cursor()
        self.maps = Maps(self.variants, self.variants_cursor, 1)
        self.maps.gen_dicts()

        self.query = query
        self.interval = interval if interval is not None else 100
        self.tid = tid
        if tid is None:
            self.tid = str(uuid4()).replace("-", "")
            execute_sql("CREATE TEMPORARY TABLE IF NOT EXISTS %s AS (%s);"
                        % (self.tid, query), self.variants, self.variants_cursor)
        self.clusters = clusters if clusters is not None else []

    @staticmethod
    def get_cluster(results, i, interval, search):
        cluster = []
        for j in range(i, 0, -1):
            if abs(results[i][search] - results[j][search]) < interval:
                cluster.append(results[j][0])
            else:
                break
        for j in range(i + 1, len(results)):
            if abs(results[i][search] - results[j][search]) < interval:
                cluster.append(results[j][0])
            else:
                break
        return cluster

    def get_core_clusters(self, results, search):
        clusters = []
        for i in range(len(results)):
            cluster = self.get_cluster(results, i, self.interval, search)
            if len(cluster) > 1:
                clusters.append(sorted(cluster))
        removed = 0
        for i in range(len(clusters)):
            i -= removed
            for j in range(len(clusters)):
                if not set(clusters[i]).issubset(set(clusters[j])) and i < j: # i > j?
                    break
                if set(clusters[i]).issubset(set(clusters[j])) and i != j:
                    del clusters[i]
                    removed += 1
                    break
        return clusters

    def set_operations(self, clusters, intersect, exclude):
        if intersect == [''] and exclude == ['']:
            return clusters
        removed = 0
        for i in range(len(clusters)):
            i -= removed
            samples = []
            for r in clusters[i]:
                sql = "select sample_id from genotype where record_id = %d" % r
                samples += [r[0] for r in query_sql(sql, self.variants, self.variants_cursor)]
            if set(intersect).issubset(set(samples)) and len(set(exclude).intersection(set(samples))) == 0:
                continue
            del clusters[i]
            removed += 1
        return clusters

    def cluster_results(self): #switch to use index in quered temptable
        ids = "select id, chrom, pos, pos2, len from" + self.query.lower().split('from')[1] #optimize for temp tables
        process = self.query.split("# ")[1].split("process")[1] if '# ' in self.query else 'include  exclude  '
        include = [int(r) if not r == '' else '' for r in process.split("include ")[1].split(" ")[0].split(",")]
        exclude = [int(r) if not r == '' else '' for r in process.split("exclude ")[1].split(" ")[0].split(",")]
        results = query_sql(ids, self.variants, self.variants_cursor)
        results = sorted(results, key=lambda element: (element[1], element[2]))
        get_chrom = itemgetter(1)
        clusters = []
        for key, chrom in groupby(results, get_chrom):
            c = list(chrom)
            clusters += self.set_operations(self.get_core_clusters(c, 2), include, exclude) #search is the field to search
        self.clusters = clusters
        return self.get_clustered_results()

    def get_results(self):
        if len(self.clusters) > 0:
            return self.cluster_results()
        results = query_sql("select * from %s" % self.tid, self.variants, self. variants_cursor)
        results = [list(r) for r in results] if results is not None else results
        return self.translate_results(results, self.get_fields())

    def get_clustered_results(self):
        output = []
        for c in self.clusters:
            cluster = []
            for rid in c:
                results = query_sql("select * from %s where id = %s" % (self.tid, rid),
                                    self.variants, self.variants_cursor)[0]
                cluster.append([list(results)] if results is not None else results)
            output.append(self.translate_results(cluster, self.get_fields()))
        return output

    def get_core_results(self):
        output = []
        for c in self.clusters:
            output.append([list(query_sql("select * from %s where id = %s" % (self.tid, c[0]),
                                          self.variants, self.variants_cursor)[0])])
        return output

    def get_fields(self):
        return [i[0] for i in self.variants_cursor.description]

    def translate_results(self, results, fields):
        print results
        t = fields.index('TYPE') if 'TYPE' in fields else -1
        f = fields.index('FILTER') if 'FILTER' in fields else -1
        g = fields.index('GT') if 'GT' in fields else -1
        s = fields.index('sample_id') if 'sample_id' in fields else -1
        id_map = Maps(self.variants, self.variants_cursor, 0)
        id_map.gen_dicts()
        for i in range(len(results)):
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
        return results

    def update(self, query):
        execute_sql("DROP TABLE %s;" % self.tid, self.variants, self.variants_cursor)
        execute_sql("CREATE TEMPORARY TABLE IF NOT EXISTS %s AS (%s);" % (self.tid, query), self.variants,
                    self.variants_cursor)
