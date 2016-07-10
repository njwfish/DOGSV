#!/usr/bin/python

import MySQLdb
import vcf
from MySQL_Utils import executeSQL, querySQL, insertSQL

class VCFtoMySQL:
	def __init__(self, ids, variant_type_mapping, core, toolInfo, toolSamples, CHROM_format, hasGT):
		self.individual_mapping = {}
		self.variant_mapping = {}
		self.alignment_location_mapping = {}
		self.tool_mapping = {}
		self.genotype_mapping = {}
		self.db = MySQLdb.connect("localhost","root","12345","DogSVStore" )
		self.cursor = self.db.cursor()
		self.CHROM_format = CHROM_format
		self.hasGT = hasGT
		self.ids = ids
		self.variant_type_mapping = variant_type_mapping
		self.core = core
		self.toolInfo = toolInfo
		self.toolSamples = toolSamples

	def getField(self, record, field):
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

	def genIndividualMap(self, vcf_reader):
		for sample in vcf_reader.samples:
			sample_id = sample.split('.')[0]
			sql = "SELECT individual_id FROM samples WHERE sample_id = '%s'" % (sample_id)
			individual_id = querySQL(sql, self.db, self.cursor)
			if len(individual_id) == 0:
				insertSQL('individuals',['sex'],['1'], self.db, self.cursor)
				individual_id = self.cursor.lastrowid
				insertSQL('samples',['sample_id', 'individual_id','tissue_type'],[str(sample_id),str(individual_id),'1'],self.db, self.cursor)
			else:
				individual_id = individual_id[0][0]
			self.individual_mapping.update({sample_id:individual_id})

	def genVariantMap(self):
		for variant in self.variant_type_mapping.values():
			sql = "SELECT variant_id FROM ref_variant WHERE type = '%s'" % (variant)
			variant_id = querySQL(sql, self.db, self.cursor)
			try:
				self.variant_mapping.update({variant:variant_id[0][0]})
			except:
				print "Error: the variant_type_mapping is incorrect."

	def genAlignmentLocationMap(self):
		sql = "SELECT location_id, type FROM ref_alignment_location"
		locations = querySQL(sql, self.db, self.cursor)
		for location in locations:
			formatLoc = str(location[1])
			if len(str(location[1])) < 3: 
				formatLoc = '%s%s' % (self.CHROM_format,str(location[1]))
			self.alignment_location_mapping.update({formatLoc:str(location[0])})

	def genToolMap(self):
		sql = "SELECT tool_id, tool FROM ref_tool"
		tools = querySQL(sql, self.db, self.cursor)
		for tool in tools:
			self.tool_mapping.update({tool[1]:tool[0]})

	def genGenotypeMap(self):
		sql = "SELECT genotype_id, genotype FROM ref_genotype"
		gts = querySQL(sql, self.db, self.cursor)
		for gt in gts:
			self.genotype_mapping.update({gt[1]:gt[0]})

	def getVariantID(self, key):
		if key in self.variant_mapping:
			return self.variant_mapping[key]
		else:
			insertSQL('ref_variant',[('type')],[(str(key))],self.db, self.cursor)
			variant_id = self.cursor.lastrowid
			self.variant_mapping.update({key:variant_id})
			return variant_id

	def getLocationID(self, key):
		if key in self.alignment_location_mapping:
			return self.alignment_location_mapping[key]
		else:
			insertSQL('ref_alignment_location',[('type')],[(str(key))],self.db, self.cursor)
			location_id = self.cursor.lastrowid
			self.alignment_location_mapping.update({key:location_id})
			return variant_id

	def setRecordID(self):
		"""Set the record_id to the autoincrement key created on the last insert."""
		self.ids['record_id'] = self.cursor.lastrowid

	def insertRecord(self, record):
		"""Adds the core fields, retrieved from the core dict,
			to the CHROM tables in the MySQL database
			:param record: the record from which to get the fields for the table
			:type record: Record
		"""
		cols = []
		vals = []
		coreVals = self.core.values()
		coreKeys = self.core.keys()
		for i in range(len(coreVals)):
			s = self.getField(record, coreVals[i])
			if 'FILTER' in coreKeys[i]:
				if s is not None:
					if len(s) == 0:
						s = 'PASS'
			if isinstance(s, list):
					if len(s) == 0:
						s = None
					else:
						s = ','.join(str(v) for v in s)
			if s is not None:
				if 'CHROM' in coreKeys[i]:
					s = self.getLocationID(s)
				if 'TYPE' in coreKeys[i]:
					s = self.getVariantID(s)
				cols.append(coreKeys[i])
				vals.append(s)
		insertSQL('records', cols, vals, self.db, self.cursor)
		self.setRecordID()
		insertSQL('tools_used',['record_id,tool'],[self.ids['record_id'],self.tool_mapping[self.ids['tool_id']]], self.db, self.cursor)

	def insertInfo(self, record):
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
			info = self.getField(record, "%s @info" % self.toolInfo[i])
			if info is not None:
				if '_L' in self.toolInfo[i]:
					for j in range(len(info)):
						cols.append('%s_%d' % (self.toolInfo[i], j))
						vals.append(info[j])
				elif isinstance(info, list):
					cols.append(self.toolInfo[i])
					vals.append(', '.join(str(v) for v in info))
				else:
					cols.append(self.toolInfo[i])
					vals.append(info)
		insertSQL("%s_info" % self.ids['tool_id'], cols, vals, self.db, self.cursor)

	def insertSampleData(self, record):
		"""Adds genotype data to genotype table and adds all the samples and tool 
			specific sample information to the tool's samples table,
			getting the fields from the toolSamples dict.
			:param record: the record to get the specified samples fields
			:type record: Record
			..warning: this assumes all the fields in toolSamples and toolInfo are
					   fields in the VCF, if not, the code will throw an error.
		"""
		for j in range(len(record.samples)):
			self.ids['individual_id'] = self.individual_mapping[record.samples[j].sample.split('.')[0]]
			# Add universally queryable genotype data to the genotype table.
			if self.hasGT:
				insertSQL('genotypes', ['individual_id', 'record_id', 'GT'], 
					[self.ids['individual_id'], self.ids['record_id'], 
					self.genotype_mapping[self.getField(record, "GT @samples %d" % (j))]], self.db, self.cursor)

			cols = ['individual_id', 'record_id']
			vals = [self.ids['individual_id'], self.ids['record_id']]
			for i in range(len(self.toolSamples)):
				field = self.getField(record, "%s @samples %d" % (self.toolSamples[i], j))
				if field is not None:
					if '_L' in self.toolSamples[i]:
						for j in range(len(field)):
							cols.append('%s_%d' % (self.toolSamples[i], j))
							vals.append(field[j])
					elif isinstance(field, list):
						cols.append(self.toolSamples[i])
						vals.append(', '.join(str(v) for v in field))
					else:
						cols.append(self.toolSamples[i])
						vals.append(field)
			insertSQL("%s_samples" % self.ids['tool_id'], cols, vals, self.db, self.cursor)

	def load(self, file):
		vcf_reader = vcf.Reader(open(file, 'r'))
		self.genIndividualMap(vcf_reader)
		self.genVariantMap()
		self.genAlignmentLocationMap()
		self.genToolMap()
		self.genGenotypeMap()
		for record in vcf_reader:
			self.insertRecord(record)
			self.insertInfo(record)
			self.insertSampleData(record)