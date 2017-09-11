import re
import yaml
from itertools import groupby
from operator import itemgetter
from uuid import uuid4
from collections import OrderedDict

import MySQLdb

from MySQL_Utils import query_sql, execute_sql
from maps import Maps


class QueryParser:
    """
    Methods to convert between a query string and the columns, table, joins, requirements, order, limit
    """
    def __init__(self):
        pass

    @staticmethod
    def parse(query):
        """
        Takes a query string and parses out the query args using regex
        :param query: string, SQL formatted query string
        :return: columns, table, joins, where, order
        """
        prog = re.compile(
            'select (.*) from (\w+) *(\w+ join \w+ on ((?!order)(?!where).)*)*(where (.*) ((?!order).)*)*(order by .*)*'
        )
        match = prog.match(query.lower()).groups(0)
        print "MATCH:", match
        columns = match[0]
        table = match[1]
        joins = match[2] if match[2] != 0 else []
        requirements = match[4] if match[4] != 0 else ''
        order = match[6] if match[4] != 0 else ''
        print "SPLIT: ", columns, table, joins, requirements, order
        return columns, table, joins, requirements, order

    @staticmethod
    def assemble(columns, table, joins, requirements, order, limit):
        """
        Takes the query args and reassembles them into a valid SQL query
        :param columns: string, comma seperate columns
        :param table: string, table name
        :param joins:
        :param requirements:
        :param order:
        :param limit:
        :return:
        """
        print "ASSEMBLE: ", columns, table, joins, requirements, order
        core = 'select %s from %s' % (columns, table)
        joins = ' '.join(list(OrderedDict.fromkeys(joins))) if isinstance(joins, list) and len(joins) > 0 else ''
        where = 'where (%s)' % requirements if isinstance(requirements, basestring) and requirements != '' else ''
        order = order if isinstance(order, basestring) else ''
        limit = limit if isinstance(limit, basestring) else ''
        return ' '.join([core, joins, where, order, limit])


class Query:
    def __init__(self, columns, table, joins, requirements, order=None, process=None, process_vars=None, tid=None):
        """

        :param columns:
        :param table:
        :param joins:
        :param requirements: set to 0 for no requirements
        :param order:
        :param process:
        :param process_vars:
        :param tid:
        """

        self.variants = MySQLdb.connect("localhost", "root", "", "dogsv")
        self.variants_cursor = self.variants.cursor()
        self.maps = Maps(self.variants, self.variants_cursor, 1)
        self.maps.gen_dicts()
        self.columns, self.table, self.joins, self.requirements, self.order = columns, table, joins, requirements, order
        self.process = process if process is not None else {}
        self.process_vars = process_vars if process_vars is not None else {}
        table_index = query_sql("show index from " + self.table, self.variants, self.variants_cursor)
        self.primary_columns = ','.join(['{0}'.format(r[4]) for r in table_index if r[2] == 'PRIMARY'])
        self.limit = "limit 5000"
        id_query = QueryParser.assemble(self.primary_columns,
                                        self.table,
                                        self.joins,
                                        self.requirements,
                                        self.order,
                                        None)
        self.tid = tid
        if self.tid is None:
            sql, self.tid = Query.get_gen_table_sql(id_query, self.primary_columns)
            execute_sql(sql, self.variants, self.variants_cursor)

    @staticmethod
    def get_gen_table_sql(query, primary_key):
        tid = "t_" + str(uuid4()).replace("-", "")
        return "CREATE TABLE IF NOT EXISTS %s (primary key(%s)) ENGINE=MyISAM AS (%s)" % (tid, primary_key, query), tid

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

    def get_sql(self):
        return QueryParser.assemble(self.columns, self.table, self.joins, self.requirements, '', '')

    def get_core_clusters(self, results, search, interval):
        clusters = []
        for i in range(len(results)):
            cluster = self.get_cluster(results, i, interval, search)
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
        ids = self.get_results(columns="id, chrom, pos, pos2, len")
        include, exclude = self.process['cluster'][0], self.process_vars['cluster'][1]
        interval = self.process['cluster'][3]
        results = query_sql(ids, self.variants, self.variants_cursor)
        results = sorted(results, key=lambda element: (element[1], element[2]))
        get_chrom = itemgetter(1)
        clusters = []
        for key, chrom in groupby(results, get_chrom):
            c = list(chrom)
            clusters += self.set_operations(self.get_core_clusters(c, 2, interval), include, exclude)
            #search is the field to search
        self.process_vars['cluster'] = clusters
        return self.get_clustered_results()

    def get_results(self, columns=None):
        columns = columns if columns is not None else str(self.columns)
        sql = QueryParser.assemble(columns.lower(), self.tid + " t", ["inner join records on t.id=records.id"] +
                                   self.joins, self.requirements, self.order, self.limit)
        #sql = "select %s from %s t left join records on t.id=records.id" % (columns.lower(), self.tid)
        results = query_sql(sql, self.variants, self.variants_cursor)
        results = [list(r) for r in results]
        fields = self.get_fields()
        return self.translate_results(results, fields), fields

    def get_clustered_results(self):
        output = []
        for c in self.process_vars['cluster']:
            cluster = []
            for rid in c:
                results = query_sql("select * from %s where id = %s" % (self.tid, rid),
                                    self.variants, self.variants_cursor)[0]
                cluster.append([list(results)] if results is not None else results)
            output.append(self.translate_results(cluster, self.get_fields()))
        fields = self.get_fields()
        return output, fields

    def get_core_results(self):
        output = []
        for c in self.process_vars['cluster']:
            output.append([list(query_sql("select * from %s where id = %s" % (self.tid, c[0]),
                                          self.variants, self.variants_cursor)[0])])
        return output

    def get_fields(self):
        return [i[0].lower() for i in self.variants_cursor.description]

    def translate_results(self, results, fields):
        t = fields.index('type') if 'type' in fields else -1
        f = fields.index('filter') if 'filter' in fields else -1
        g = fields.index('gt') if 'gt' in fields else -1
        s = fields.index('sample_id') if 'sample_id' in fields else -1
        id_map = Maps(self.variants, self.variants_cursor, 0)
        id_map.gen_dicts()
        for i in range(len(results)):
            if t > -1:
                results[i][t] = id_map.variant_mapping[results[i][t]] \
                    if results[i][t] in id_map.variant_mapping else 'None'
            if f > -1:
                results[i][f] = id_map.filter_mapping[results[i][f]] \
                    if results[i][f] in id_map.filter_mapping else 'None'
            if g > -1:
                results[i][g] = id_map.genotype_mapping[results[i][g]] \
                    if results[i][g] in id_map.genotype_mapping else 'None'
            if s > -1:
                results[i][s] = id_map.sample_mapping[results[i][s]] \
                    if results[i][s] in id_map.sample_mapping else 'None'
        return results

    def sub_query(self, columns, joins, requirements):
        joins.insert(0, 'left join records on t.id=records.id')
        subquery = QueryParser.assemble(self.primary_columns, self.tid + " t", joins, requirements, None, 'limit 5000')
        sql, tid = Query.get_gen_table_sql(subquery, self.primary_columns)
        execute_sql(sql, self.variants, self.variants_cursor)
        return Query(columns, self.table, joins, requirements, None, tid=tid)
