#!/usr/bin/python

import MySQLdb
import vcf
from MySQL_Utils import query_sql, insert_sql


class VCFtoMySQL:
    def __init__(self, ids, variant_type_mapping, core, toolInfo, toolSamples, CHROM_format, hasGT):
        self.sample_mapping = {}
        self.variant_mapping = {}
        self.alignment_location_mapping = {}
        self.tool_mapping = {}
        self.genotype_mapping = {}
        self.filter_mapping = {}
        self.db = MySQLdb.connect("localhost", "root", "12345", "DogSVStore")
        self.cursor = self.db.cursor()
        self.CHROM_format = CHROM_format
        self.hasGT = hasGT
        self.ids = ids
        self.variant_type_mapping = variant_type_mapping
        self.core = core
        self.toolInfo = toolInfo
        self.toolSamples = toolSamples

    @staticmethod
    def get_field(record, field):
        """Get the specified field from the given record using the
            getattr method (this is done purely to make the script facile to edit).
            :param record: the record from which to get the field
            :type record: Record
            :param field: the field to get from the record
            :type field: string
            :return: the field retrieved from the record
            :rtype: string
        """
        # Split the first section of the string: the field to be retrieved.
        key = field.split(' ')[0]
        if '@info' in field:
            # Retrieve the field from the INFO dict, created by PyVCF
            if key in record.INFO:
                return record.INFO[key]
        elif '@samples' in field:
            # Retrieve the field from the samples list, then from the Call class
            # get the data tuple and extract the field created by PyVCF.
            try:
                return getattr(record.samples[int(field.split(' ')[2])].data, key)
            except:
                return None
        else:
            return getattr(record, key)
        return None

    def gen_individual_map(self, vcf_reader):
        for sample in vcf_reader.samples:
            str_sample_id = sample.split('.')[0]
            sql = "SELECT sample_id FROM ref_sample WHERE sample = '%s'" % str_sample_id
            sample_id = query_sql(sql, self.db, self.cursor)
            if len(sample_id) == 0:
                insert_sql('individuals', ['sex'], ['1'], self.db, self.cursor)
                individual_id = self.cursor.lastrowid
                insert_sql('ref_sample', ['sample'], [str_sample_id], self.db, self.cursor)
                sample_id = self.cursor.lastrowid
                insert_sql('samples', ['sample_id, individual_id'],
                           [str(sample_id), str(individual_id)], self.db, self.cursor)
            else:
                sample_id = sample_id[0][0]
            self.sample_mapping.update({str_sample_id: sample_id})

    def gen_variant_map(self):
        for variant in self.variant_type_mapping.values():
            sql = "SELECT variant_id FROM ref_variant WHERE variant = '%s'" % variant
            variant_id = query_sql(sql, self.db, self.cursor)
            try:
                self.variant_mapping.update({variant: variant_id[0][0]})
            except:
                print "Error: the variant_type_mapping is incorrect."

    def gen_alignment_location_map(self):
        sql = "SELECT location_id, location FROM ref_alignment_location"
        locations = query_sql(sql, self.db, self.cursor)
        for location in locations:
            format_loc = str(location[1])
            if len(str(location[1])) < 3:
                format_loc = '%s%s' % (self.CHROM_format, str(location[1]))
            self.alignment_location_mapping.update({format_loc: str(location[0])})

    def gen_tool_map(self):
        sql = "SELECT tool_id, tool FROM ref_tool"
        tools = query_sql(sql, self.db, self.cursor)
        for tool in tools:
            self.tool_mapping.update({tool[1]: tool[0]})

    def gen_genotype_map(self):
        sql = "SELECT genotype_id, genotype FROM ref_genotype"
        gts = query_sql(sql, self.db, self.cursor)
        for gt in gts:
            self.genotype_mapping.update({gt[1]: gt[0]})

    def gen_filter_map(self):
        sql = "SELECT filter_id, filter FROM ref_filter"
        filters = query_sql(sql, self.db, self.cursor)
        for filter in filters:
            self.filter_mapping.update({filter[1]: filter[0]})

    def get_variant_id(self, key):
        if key in self.variant_mapping:
            return self.variant_mapping[key]
        else:
            print "Inserted ref_variant:", [(str(key))]
            insert_sql('ref_variant', ['variant'], [(str(key))], self.db, self.cursor)
            variant_id = self.cursor.lastrowid
            self.variant_mapping.update({key: variant_id})
            return variant_id

    def get_location_id(self, key):
        if key in self.alignment_location_mapping:
            return self.alignment_location_mapping[key]
        else:
            print "Inserted ref_alignment_location:", [(str(key))]
            insert_sql('ref_alignment_location', ['location'],
                       [(str(key)).split(self.CHROM_format)[1]], self.db, self.cursor)
            location_id = self.cursor.lastrowid
            self.alignment_location_mapping.update({key:location_id})
            return location_id

    def get_filter_id(self, key):
        if key in self.filter_mapping:
            return self.filter_mapping[key]
        else:
            print "Inserted ref_filter:", [(str(key))]
            insert_sql('ref_filter', ['filter'], [(str(key))], self.db, self.cursor)
            filter_id = self.cursor.lastrowid
            self.filter_mapping.update({key:filter_id})
            return filter_id

    def set_record_id(self):
        """Set the record_id to the autoincrement key created on the last insert."""
        self.ids['record_id'] = self.cursor.lastrowid

    def insert_record(self, record):
        """Adds the core fields, retrieved from the core dict,
            to the CHROM tables in the MySQL database
            :param record: the record from which to get the fields for the table
            :type record: Record
        """
        cols = []
        vals = []
        core_vals = self.core.values()
        core_keys = self.core.keys()
        for i in range(len(core_vals)):
            s = self.get_field(record, core_vals[i])
            if 'FILTER' in core_keys[i]:
                if s is not None:
                    if len(s) == 0:
                        s = 'PASS'
            if isinstance(s, list):
                    if len(s) == 0:
                        s = None
                    else:
                        s = ','.join(str(v) for v in s)
            if s is not None:
                if 'CHROM' in core_keys[i]:
                    s = self.get_location_id(s)
                elif 'TYPE' in core_keys[i]:
                    s = self.get_variant_id(self.variant_type_mapping[s])
                elif 'FILTER' in core_keys[i]:
                    s = self.get_filter_id(s)
                cols.append(core_keys[i])
                vals.append(s)
        insert_sql('records', cols, vals, self.db, self.cursor)
        self.set_record_id()
        insert_sql('tools_used', ['record_id,tool'],
                   [self.ids['record_id'], self.tool_mapping[self.ids['tool_id']]], self.db, self.cursor)

    def insert_info(self, record):
        """Adds the unique, tool specific information to the tool's INFO table,
            from toolInfo dict.
            :param record: the record to get the specified INFO fields
            :type record: Record
            ..warning: this assumes all the fields in toolSamples and toolInfo are
                       fields in the VCF, if not, the code will throw an error.
        """
        cols = ['record_id']
        vals = [self.ids['record_id']]
        for i in range(len(self.toolInfo)):
            info = self.get_field(record, "%s @info" % self.toolInfo[i].split('_L')[0])
            if info is not None:
                if '_L' in self.toolInfo[i]:
                    for j in range(len(info)):
                        cols.append('%s_%d' % (self.toolInfo[i].split('_L')[0], j))
                        vals.append(info[j])
                elif isinstance(info, list):
                    cols.append(self.toolInfo[i])
                    vals.append(', '.join(str(v) for v in info))
                else:
                    cols.append(self.toolInfo[i])
                    vals.append(info)
        insert_sql("%s_info" % self.ids['tool_id'], cols, vals, self.db, self.cursor)

    def insert_sample_data(self, record):
        """Adds genotype data to genotype table and adds all the samples and tool
            specific sample information to the tool's samples table,
            getting the fields from the toolSamples dict.
            :param record: the record to get the specified samples fields
            :type record: Record
            ..warning: this assumes all the fields in toolSamples and toolInfo are
                       fields in the VCF, if not, the code will throw an error.
        """
        for j in range(len(record.samples)):
            self.ids['sample_id'] = self.sample_mapping[record.samples[j].sample.split('.')[0]]
            # Add universally query-able genotype data to the genotype table.
            if self.hasGT:
                insert_sql('genotype', ['sample_id', 'record_id', 'GT'],
                           [self.ids['sample_id'], self.ids['record_id'],
                           self.genotype_mapping[self.get_field(record, "GT @samples %d" % j)]], self.db, self.cursor)
            else:
                insert_sql('genotype', ['sample_id', 'record_id'],
                           [self.ids['sample_id'], self.ids['record_id']], self.db, self.cursor)

            cols = ['sample_id', 'record_id']
            vals = [self.ids['sample_id'], self.ids['record_id']]
            for i in range(len(self.toolSamples)):
                field = self.get_field(record, "%s @samples %d" % (self.toolSamples[i].split('_L')[0], j))
                if field is not None:
                    if '_L' in self.toolSamples[i]:
                        for k in range(len(field)):
                            cols.append('%s_%d' % (self.toolSamples[i].split('_L')[0], k))
                            vals.append(field[k])
                    elif isinstance(field, list):
                        cols.append(self.toolSamples[i])
                        vals.append(', '.join(str(v) for v in field))
                    else:
                        cols.append(self.toolSamples[i])
                        vals.append(field)
            insert_sql("%s_samples" % self.ids['tool_id'], cols, vals, self.db, self.cursor)

    def load(self, file):
        vcf_reader = vcf.Reader(open(file, 'r'))
        self.gen_individual_map(vcf_reader)
        self.gen_variant_map()
        self.gen_alignment_location_map()
        self.gen_tool_map()
        self.gen_genotype_map()
        self.gen_filter_map()
        for record in vcf_reader:
            self.insert_record(record)
            self.insert_info(record)
            self.insert_sample_data(record)