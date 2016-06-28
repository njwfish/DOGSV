#!/usr/bin/python

import MySQLdb
import vcf
import sys
import getopt
import glob, os

#TODO: Change tool_id value to the ID of the correct tool
ids = {
	'individual_id': 	'UNKN0001',
	'variant_id':		'0',
	'tool_id': 			'LMP',  #TODO: update
}

#TODO: Add variant types specific to this tool on the left,
#		and the type (one of the seven listed below) it is equivalent to
#		on the right. Do not delete any of the current fields.
variant_mapping = {
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

individual_mapping = {
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
	'IMPRECISE',
	'CIPOS',
	'CIEND',
	'CIPOS95',
	'CIEND95',
	'MATEID',
	'SECONDARY',
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
	'GT',
	'SU',
	'PE',
	'SR',
	'BD'
]

################################################################################
#   DO NOT CHANGE ANYTHING BELOW THIS LINE UNLESS YOU KNOW WHAT YOU'RE DOING   #
################################################################################

#db = MySQLdb.connect("localhost","root","12345","DogSVStore" )
#cursor = db.cursor()

def executeSQL(sql):
	"""This executes a passed string via cursor
		:param sql: the query to be executed
		:type sql: string
	"""
	try:
		#cursor.execute(sql)
		#db.commit()
		print sql
	except:
		# Rollback (undo changes) in case there is any error
		print "Error: rolling back..."
		#db.rollback()
	return

def insertSQL(table, cols, vals):
	"""Attempt to add val to col in table in database via cursor
		:param table: a table in the connected MySQL database
		:type table: string
		:param col: the columns in the selected table
		:type col: string list
		:param vals: the vals, in the same order as the columns, for the table
		:type vals: string list
	"""
	sql = "INSERT INTO '%s'('%s') VALUES ('%s')" % (
			table, ', '.join(cols), ', '.join(vals))
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
		return getattr(record.samples[int(field.split(' ')[2])].data, key)
	else:
		return getattr(record, key)
	return None

def genIndividualMap(record):
	for sample in record.samples:
		sql = "SELECT individual_id FROM individuals WHERE file = '%s'" % (file)
		try:
			cursor.execute(sql)
			results = cursor.fetchall()
			individual_mapping.update({sample.sample:results[0][0]})
				
		except:
			print "Error: unable to fecth data"


def setVariantID():
	"""Set the variant_id to the autoincrement key created on the last insert."""
	#ids['variant_id'] = cursor.lastrowid

def insertCore(record):
	"""Adds the core fields, retrieved from the core dict,
		to the CHROM tables in the MySQL database
		:param record: the record from which to get the fields for the table
		:type record: Record
	"""
	cols = []
	vals = []
	valKeys = core.values()
	for i in range(len(valKeys)):
		s = getField(record, valKeys[i])
		if s is not None:
			cols.append(core.keys()[i])
			vals.append(str(s))
	insertSQL('variants', cols, vals)

def insertInfo(record):
	"""Adds the unique, tool specific information to the tool's INFO table,
		from toolInfo dict.
		:param record: the record to get the specified INFO fields
		:type record: Record
		..warning: this assumes all the fields in toolSamples and toolInfo are
				   fields in the VCF, if not, the code will throw an error.
	"""
	cols = ['variant_id']
	vals = [ids['variant_id']]
	for i in range(len(toolInfo)):
		info = getField(record, "%s @info" % toolInfo[i])
		if info is not None:
			cols.append(toolInfo[i])
			vals.append(str(info))
	insertSQL("%s.INFO" % ids['tool_id'], cols, vals)

def insertSamples(record):
	"""Adds genotype data to genotype table and adds all the samples and tool 
		specific sample information to the tool's samples table,
		getting the fields from the toolSamples dict.
		:param record: the record to get the specified samples fields
		:type record: Record
		..warning: this assumes all the fields in toolSamples and toolInfo are
				   fields in the VCF, if not, the code will throw an error.
	"""
	for j in range(len(record.samples)):
		ids['individual_id'] = individual_mapping[record.samples[j].sample]
		# Add universally queryable genotype data to the genotype table.
		insertSQL('genotype', ['individual_id', 'variant_id', 'GT'], [ids[individual_id], ids[variant_id], getField(record, "GT @samples %d" % (j))])
		cols = ['individual_id', 'variant_id']
		vals = [ids['individual_id'], ids['variant_id']]
		for i in range(len(toolSamples)):
			field = getField(record, "%s @samples %d" % (toolSamples[i], j))
			if field is not None:
				cols.append(toolSamples[i])
				vals.append(str(field))
		insertSQL("%s.samples" % ids['tool_id'], cols, vals)

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
	parseOptions(argv)
	for file in glob.glob("*.vcf"):
		vcf_reader = vcf.Reader(open(file, 'r'))
		for record in vcf_reader:
			insertCore(record)
			setVariantID()
			insertInfo(record)
			insertSamples(record)

if __name__ == "__main__":
	main(sys.argv[1:])
