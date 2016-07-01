#!/usr/bin/python

import MySQLdb
import vcf
import sys
import getopt
import glob, os

CHROM_format = 'chr'
hasGT = True

#TODO: Change tool_id value to the ID of the correct tool
ids = {
	'individual_id': 	'UNKN0001',
	'variant_id':		'0',
	'tool_id': 			'LMP',  #TODO: update
}

#TODO: Add variant types specific to this tool on the left,
#		and the type (one of the seven listed below) it is equivalent to
#		on the right. Do not delete any of the current fields.
variant_type_mapping = {
	'DEL':'DEL',
	'DUP':'DUP',
	'INS':'INS',
	'INV':'INV',
	'TRA':'TRA',
	'SIN':'SIN',
	'LIN':'LIN',
	'BXP':'BXP',
	'DUP:TANDEM':'DUP',
	'CNV':'UKN'
}

#TODO: Change the right side of the values to be updated to the correct
#		corresponding fields. Use @info is it is in the INFO secion, and
#		@samples if it is in the SAMPLES section.
#		Likely the only fields that will change are CHROM2, POS2, and LEN.
#		If there are no corresponding fields, delete the whole line. For
#		example, if there is no LEN corollary in this VCF, then dont leave
#		'LEN': '', simply delete that line from the declaration.
core = {
	'CHROM':	'CHROM',
	'POS': 		'POS',
	'REF': 		'REF',
	'ALT': 		'ALT',
	'QUAL': 	'QUAL',
	'FILTER': 	'FILTER',
	'TYPE':		'SVTYPE @info',	#TODO: update
	'CHROM2': 	'CHR2 @info', 	#TODO: update
	'POS2': 	'END @info', 	#TODO: update
	'LEN': 		'LEN @info'		#TODO: update
}

#TODO: Replace and extend all these placeholder values with the actual fields
#		from the INFO section of the VCF. Anything not added will not go into
#		the database.
toolInfo = [
	'STRANDS',
	'CIPOS_L',
	'CIEND_L',
	'CIPOS95_L',
	'CIEND95_L',
	'MATEID',
	'SU',
	'PE',
	'SR',
	'EV',
	'PRPOS',
	'PREND'
]

#TODO: Replace and extend all these placeholder values with the actual fields
#		from the SAMPLES section of the VCF. Anything not added will not go into
#		the database.
toolSamples = [
	'SU',
	'PE',
	'SR',
	'BD'
]

################################################################################
#   DO NOT CHANGE ANYTHING BELOW THIS LINE UNLESS YOU KNOW WHAT YOU'RE DOING   #
################################################################################
individual_mapping = {}
variant_mapping = {}
alignment_location_mapping = {}
tool_mapping = {}
genotype_mapping = {}
db = MySQLdb.connect("localhost","root","12345","DogSVStore" )
cursor = db.cursor()

def executeSQL(sql):
	"""This executes a passed string via cursor
		:param sql: the query to be executed
		:type sql: string
	"""
	try:
		cursor.execute(sql)
		db.commit()
	except:
		# Rollback (undo changes) in case there is any error
		print "Error: rolling back..."
		print sql
		db.rollback()

def querySQL(sql):
	try:
		cursor.execute(sql)
		return cursor.fetchall()
	except:
		print "Error: unable to fecth data"
	return None

def insertSQL(table, cols, vals):
	"""Attempt to add val to col in table in database via cursor
		:param table: a table in the connected MySQL database
		:type table: string
		:param col: the columns in the selected table
		:type col: string list
		:param vals: the vals, in the same order as the columns, for the table
		:type vals: string list
	"""
	sql = "INSERT INTO %s(%s) VALUES ('%s')" % (
			table, ', '.join(cols), '\', \''.join(str(v) for v in vals))
	executeSQL(sql)

def getField(record, field):
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

def genIndividualMap(vcf_reader):
	for sample in vcf_reader.samples:
		sample_id = sample.split('.')[0]
		sql = "SELECT individual_id FROM samples WHERE sample_id = '%s'" % (sample_id)
		individual_id = querySQL(sql)
		if len(individual_id) == 0:
			insertSQL('individuals',['sex'],['1'])
			individual_id = cursor.lastrowid
			insertSQL('samples',['sample_id', 'individual_id','tissue_type'],[str(sample_id),str(individual_id),'1'])
		else:
			individual_id = individual_id[0][0]
		individual_mapping.update({sample_id:individual_id})

def genVariantMap():
	for variant in variant_type_mapping.values():
		sql = "SELECT variant_id FROM ref_variant WHERE type = '%s'" % (variant)
		variant_id = querySQL(sql)
		try:
			variant_mapping.update({variant:variant_id[0][0]})
		except:
			print "Error: the variant_type_mapping is incorrect."

def genAlignmentLocationMap():
	sql = "SELECT location_id, type FROM ref_alignment_location"
	locations = querySQL(sql)
	for location in locations:
		formatLoc = str(location[1])
		if len(str(location[1])) < 3: 
			formatLoc = '%s%s' % (CHROM_format,str(location[1]))
		alignment_location_mapping.update({formatLoc:str(location[0])})

def genToolMap():
	sql = "SELECT tool_id, tool FROM ref_tool"
	tools = querySQL(sql)
	for tool in tools:
		tool_mapping.update({tool[1]:tool[0]})

def genGenotypeMap():
	sql = "SELECT genotype_id, genotype FROM ref_genotype"
	gts = querySQL(sql)
	for gt in gts:
		genotype_mapping.update({gt[1]:gt[0]})

def getVariantID(key):
	if key in variant_mapping:
		return variant_mapping[key]
	else:
		insertSQL('ref_variant',[('type')],[(str(key))])
		variant_id = cursor.lastrowid
		variant_mapping.update({key:variant_id})
		return variant_id

def getLocationID(key):
	if key in alignment_location_mapping:
		return alignment_location_mapping[key]
	else:
		insertSQL('ref_alignment_location',[('type')],[(str(key))])
		location_id = cursor.lastrowid
		alignment_location_mapping.update({key:location_id})
		return variant_id

def setRecordID():
	"""Set the record_id to the autoincrement key created on the last insert."""
	ids['record_id'] = cursor.lastrowid

def insertRecord(record):
	"""Adds the core fields, retrieved from the core dict,
		to the CHROM tables in the MySQL database
		:param record: the record from which to get the fields for the table
		:type record: Record
	"""
	cols = []
	vals = []
	coreVals = core.values()
	coreKeys = core.keys()
	for i in range(len(coreVals)):
		s = getField(record, coreVals[i])
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
				s = getLocationID(s)
			if 'TYPE' in coreKeys[i]:
				s = getVariantID(s)
			cols.append(coreKeys[i])
			vals.append(s)
	insertSQL('records', cols, vals)
	setRecordID()
	insertSQL('tools_used',['record_id,tool'],[ids['record_id'],tool_mapping[ids['tool_id']]])

def insertInfo(record):
	"""Adds the unique, tool specific information to the tool's INFO table,
		from toolInfo dict.
		:param record: the record to get the specified INFO fields
		:type record: Record
		..warning: this assumes all the fields in toolSamples and toolInfo are
				   fields in the VCF, if not, the code will throw an error.
	"""
	cols = ['record_id']
	vals = [ids['record_id']]
	for i in range(len(toolInfo)):
		info = getField(record, "%s @info" % toolInfo[i])
		if info is not None:
			if '_L' in toolInfo[i]:
				for j in range(len(info)):
					cols.append('%s_%d' % (toolInfo[i], j))
					vals.append(info[j])
			elif isinstance(info, list):
				cols.append(toolInfo[i])
				vals.append(', '.join(str(v) for v in info))
			else:
				cols.append(toolInfo[i])
				vals.append(info)
	insertSQL("%s_info" % ids['tool_id'], cols, vals)

def insertSampleData(record):
	"""Adds genotype data to genotype table and adds all the samples and tool 
		specific sample information to the tool's samples table,
		getting the fields from the toolSamples dict.
		:param record: the record to get the specified samples fields
		:type record: Record
		..warning: this assumes all the fields in toolSamples and toolInfo are
				   fields in the VCF, if not, the code will throw an error.
	"""
	for j in range(len(record.samples)):
		ids['individual_id'] = individual_mapping[record.samples[j].sample.split('.')[0]]
		# Add universally queryable genotype data to the genotype table.
		if hasGT:
			insertSQL('genotypes', ['individual_id', 'record_id', 'GT'], 
				[ids['individual_id'], ids['record_id'], 
				genotype_mapping[getField(record, "GT @samples %d" % (j))]])

		cols = ['individual_id', 'record_id']
		vals = [ids['individual_id'], ids['record_id']]
		for i in range(len(toolSamples)):
			field = getField(record, "%s @samples %d" % (toolSamples[i], j))
			if field is not None:
				if '_L' in toolSamples[i]:
					for j in range(len(field)):
						cols.append('%s_%d' % (toolSamples[i], j))
						vals.append(field[j])
				elif isinstance(field, list):
					cols.append(toolSamples[i])
					vals.append(', '.join(str(v) for v in field))
				else:
					cols.append(toolSamples[i])
					vals.append(field)
		insertSQL("%s_samples" % ids['tool_id'], cols, vals)

def parseOptions(argv):
	"""Parse the command line arguments for this script.
		Current arguments:
			-i: 				individual id
			--individual:		individual id
		:param argv: the arguments string to be parsed
		:type argv: string
	"""
	try:
		opts, args = getopt.getopt(argv,"hi:",["individual="])
	except getopt.GetoptError:
		print 'test.py -i <individual>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'test.py -i <individual>'
			sys.exit()
		elif opt in ("-i", "--individual"):
			ids['individual_id'] = arg

def main(argv):
	for file in glob.glob("*.vcf"):
		vcf_reader = vcf.Reader(open(file, 'r'))
		parseOptions(argv)
		genIndividualMap(vcf_reader)
		genVariantMap()
		genAlignmentLocationMap()
		genToolMap()
		genGenotypeMap()
		for record in vcf_reader:
			insertRecord(record)
			insertInfo(record)
			insertSampleData(record)

if __name__ == "__main__":
	main(sys.argv[1:])