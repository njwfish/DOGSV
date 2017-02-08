#!/usr/bin/python

import MySQLdb
from MySQL_Utils import query_sql
from maps import Maps
from collections import defaultdict, namedtuple
import re
from zipfile import ZipFile
import os


class SQLtoVCF:
    def __init__(self, query, output, prefix_chrom, all_info):
        self.db = MySQLdb.connect("localhost", "root", "12345", "DogSVStore")
        self.cursor = self.db.cursor()
        self.query = query
        self.prefix_chrom = prefix_chrom
        self.all_info = all_info
        self.tables = []
        self.maps = Maps(self.db, self.cursor, 0)
        self.maps.gen_dicts()
        self.columns = defaultdict(list)
        self.column_info = {}
        self.merges = defaultdict(list)
        self.output = output
        self.files = []

    def gen_tables(self, tool):
        self.tables = ['genotype', '%s_info' % tool.lower(), '%s_samples' % tool.lower()]

    def gen_cols(self):
        self.columns = defaultdict(list)
        self.column_info = {}
        for t in self.tables:
            sql = "SELECT column_name, data_type, column_comment from information_schema.columns where " \
                  "table_schema='DogSVStore' and table_name='%s';" % t
            results = query_sql(sql, self.db, self.cursor)
            for c in results:
                if '_id' not in c:
                    self.columns[t].append(c[0])
                    Column = namedtuple('Column', 'data_type comment')
                    self.column_info.update({c[0]: Column(c[1], c[2])})

    def gen_merges(self):
        self.merges = defaultdict(list)
        for t in self.tables:
            for i in range(len(self.columns[t])):
                c = self.columns[t][i]
                if re.match('.+_\d+', c) and i not in [v for r in self.merges[t] for v in r]:
                    List_Column = namedtuple('List_Column', 'column index')
                    col_merge = List_Column(c.split('_')[0], c.split('_')[1])
                    to_merge = [i]
                    for j in range(i + 1, len(self.columns[t])):
                        if col_merge.column in self.columns[t][j]:
                            to_merge.append(j)
                        else:
                            break
                    self.merges[t].append(to_merge)
        for m in self.merges.keys():
            removed = 0
            for i in self.merges[m]:
                i = [v - removed for v in i]
                c = self.columns[m][i[0]].split('_')[0]
                self.column_info[c] = self.column_info.pop(self.columns[m][i[0]])
                self.columns[m][i[0]] = c
                for j in range(1, len(i)):
                    del self.column_info[self.columns[m].pop(i[j] - (j - 1))]
                    removed += 1

    @staticmethod
    def merge(vals, merges):
        removed = 0
        for i in merges:
            i = [v - removed for v in i]
            for j in range(1, len(i)):
                vals[i[0]] = str(vals[i[0]]) + ',' + str(vals.pop(i[j - (j - 1)]))
                removed += 1
        return vals

    def merge_cols(self, record):
        for t in self.merges.keys():
            if '_samples' in t or 'genotype' in t:
                for i in range(len(record[t])):
                    record[t][i] = self.merge(record[t][i], self.merges[t])
            else:
                record[t] = self.merge(record[t], self.merges[t])
        return record

    def get_mapping(self, record):
        record['records'][7] = self.maps.variant_mapping[record['records'][7]] \
            if record['records'][7] is not None else '.'
        record['records'][6] = self.maps.filter_mapping[record['records'][6]] \
            if record['records'][6] is not None else '.'
        record['records'][0] = self.maps.alignment_location_mapping[record['records'][0]] \
            if record['records'][0] is not None else '.'
        for i in range(len(record['records'])):
            record['records'][i] = str(record['records'][i]) if record['records'][i] is not None else '.'
        for i in range(len(record['genotype'])):
            record['genotype'][i][2] = self.maps.genotype_mapping[record['genotype'][i][2]]
        return self.merge_cols(record)

    def get_by_id(self, id):
        """Gets a record from a given ID"""
        record = {}
        sql = "select * from records where id = %d" % id
        record.update({'records': list(query_sql(sql, self.db, self.cursor)[0])})

        for t in self.tables:
            sql = "select * from %s where record_id = %d" % (t, id)
            if '_samples' in t or t == 'genotype':
                record.update({t.lower(): [[v for v in r] for r in query_sql(sql, self.db, self.cursor)]})
            else:
                record.update({t.lower(): list(query_sql(sql, self.db, self.cursor)[0])})
        return self.get_mapping(record)

    def get_fks(self, ids):
        """Gets all samples in list of IDs
        TODO: Make this permanent storage so as not to overflow memory"""
        SAMPLES = defaultdict(list)
        TOOLS = defaultdict(list)
        for ID in ids:
            sql = "select tool from tools_used where record_id = %s" % ID
            for t in query_sql(sql, self.db, self.cursor):
                tool = self.maps.tool_mapping[t[0]]
                if t[0] not in TOOLS:
                    TOOLS[tool].append(ID)
                sql = "select sample_id from genotype where record_id = %s" % ID
                for s in query_sql(sql, self.db, self.cursor):
                    if s[0] not in SAMPLES[tool]:
                        SAMPLES[tool].append(s[0])
        return SAMPLES, TOOLS

    def sql_to_vcf(self):
        get_ids = "select id from" + self.query.lower().split('from')[1]
        results = [r[0] for r in query_sql(get_ids, self.db, self.cursor)]
        SAMPLES, TOOLS = self.get_fks(results)
        for tool in TOOLS.keys():
            self.gen_tables(tool)
            self.gen_cols()
            self.gen_merges()
            self.files.append(tool + '.' + self.output + '.vcf')
            with open(self.files[-1], 'w') as writer:
                # Write the VCF header.
                writer.write('##fileformat=VCFv4.2')
                writer.write('\n##INFO=<ID=CHR2,Number=1,Type=Integer,Description="Chromosome of the end position of the '
                             'variant described in this record.">')
                writer.write('\n##INFO=<ID=POS2,Number=1,Type=Integer,Description="Either the end of the variant or the '
                             'position of the translocation on the second chromosome.">')
                writer.write('\n##INFO=<ID=TYPE,Number=1,Type=String,Description="Type of structural variant.">')
                writer.write('\n##INFO=<ID=LEN,Number=1,Type=Integer,Description="The length of the structural variant.">')
                for t in self.tables:
                    if '_info' in t:
                        for c in self.columns[t]:
                            writer.write('\n##INFO=<ID=%s,Number=1,Type=%s,Description="%s">'
                                         % (c, self.column_info[c].data_type, self.column_info[c].comment))
                sql = "select variant, unabbreviated FROM ref_variant"
                for v in query_sql(sql, self.db, self.cursor):
                    writer.write('\n##ALT=<ID=%s,Description="%s">' % (v[0], v[1]))
                writer.write('\n##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">')
                for t in self.tables:
                    if '_samples' in t:
                        for c in self.columns[t]:
                            writer.write('\n##FORMAT=<ID=%s,Number=1,Type=%s,Description="%s">'
                                         % (c, self.column_info[c].data_type, self.column_info[c].comment))
                vcf_fields = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'FORMAT']
                vcf_fields = vcf_fields + [self.maps.sample_mapping[s] for s in SAMPLES[tool]]
                # Write the VCF fields and samples
                writer.write('\n#%s\n' % '\t'.join(vcf_fields))
                # For each record parse out the VCF fields and FORMAT fields from the samples
                prev_ID = -1
                for ID in TOOLS[tool]:
                    if int(prev_ID) == int(ID):
                        continue
                    prev_ID = ID
                    record = self.get_by_id(ID)
                    CHROM = record['records'][0]
                    POS = record['records'][1]
                    REF = record['records'][3]
                    ALT = record['records'][4]
                    QUAL = record['records'][5]
                    FILTER = record['records'][6]

                    INFO_cols = ['CHR2', 'POS2', 'TYPE', 'LEN']
                    INFO_vals = [record['records'][8], record['records'][9], record['records'][7], record['records'][10]]

                    for t in self.tables:
                        if '_info' in t:
                            INFO_cols = INFO_cols + self.columns[t][1:]
                            INFO_vals = INFO_vals + record[t][1:]

                    INFO = []
                    for i in range(len(INFO_cols)):
                        if INFO_vals[i] is not None or self.all_info:
                            INFO.append(INFO_cols[i] + '=' + str(INFO_vals[i] if INFO_vals[i] is not None else '.'))
                    INFO = ';'.join(INFO)

                    FORMAT_cols = {}
                    FORMAT_vals = defaultdict(lambda: defaultdict(list))

                    for t in self.tables:
                        if '_samples' in t or t == 'genotype':
                            FORMAT_cols.update({t: self.columns[t]})
                            for r in record[t]:
                                    FORMAT_vals[t][r[0]] = r[2:]
                            for s in SAMPLES[tool]:
                                if s not in FORMAT_vals[t]:
                                    FORMAT_vals[t].update({s: ['.' for c in FORMAT_cols[t]]})

                    FORMAT_dict = defaultdict(list)
                    FORMAT = []
                    for t in self.tables:
                        if '_samples' in t or t == 'genotype':
                            FORMAT.append(';'.join(self.columns[t][2:]))
                    FORMAT = ';'.join(FORMAT)
                    for t in FORMAT_vals.keys():
                        for s in FORMAT_vals[t]:
                            FORMAT_dict[s].append(';'.join([str(v) for v in FORMAT_vals[t][s]]))
                    for s in SAMPLES[tool]:
                        FORMAT += '\t' + ';'.join(FORMAT_dict[s])
                    prefix = 'chr' if self.prefix_chrom else ''
                    writer.write("\t".join([prefix + CHROM, POS, str(ID), REF, ALT, QUAL, FILTER, INFO, FORMAT]) + "\n")
        with ZipFile('app/static/' + self.output + '.zip', 'w') as out:
            for f in self.files:
                out.write(f)
                os.remove(f)
        return self.output + '.zip'
