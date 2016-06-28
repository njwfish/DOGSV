import getopt
import csv
import os.path
import sys
from itertools import islice

files = {
	'itsv':'',
	'ovcf':''
}
samples = []
command = []

def genReaderDict():
	""""""
	with open(files['itsv'], "r") as tsv:
		#Skip over the header of the Breakdancer file
		i = 0 # To keep track of position in the file for slicing
		for line in tsv.readlines():
			i += 1
			if '#Chr1' in line: # This will be the fields line, right the before data
				fields = line[1:].split() # Remove #
				break
			if '#Command:' in line:
				command.append(line[10:]) #10 characters in '#Command: '
		tsv.close()
		tsv = islice(open(files['itsv'], "r"), i, None)
		for j in range(len(fields)):
			fields[j] = str(fields[j].split('.')[0])
			if j > 10:
				samples.append(fields[j])
		return csv.DictReader(tsv, fieldnames = fields, dialect="excel-tab")

def parseTSV(tsv):
	with open(files['ovcf'], 'w+') as writer:
		writer.write('##fileformat=VCFv4.2')
		writer.write('\n##INFO=<ID=ORIENTATION1,Number=1,Type=String,Description="The number of reads mapped to the plus (+) or the minus (-) strand in the anchoring regions.">')
		writer.write('\n##INFO=<ID=CHR2,Number=1,Type=Integer,Description="Chromosome of the end position of the variant described in this record.">')
		writer.write('\n##INFO=<ID=POS2,Number=1,Type=Integer,Description="End position of the variant described in this record.">')
		writer.write('\n##INFO=<ID=ORIENTATION2,Number=1,Type=String,Description="The number of reads mapped to the plus (+) or the minus (-) strand in the anchoring regions.">')
		writer.write('\n##INFO=<ID=TYPE,Number=1,Type=String,Description="Type of structural variant.">')
		writer.write('\n##INFO=<ID=SIZE,Number=.,Type=Integer,Description="Size of the SV in base pairs.  It is meaningless for inter-chromosomal translocations.">')
		writer.write('\n##INFO=<ID=SCORE,Number=1,Type=Integer,Description="The confidence score associated with the prediction.">')
		writer.write('\n##INFO=<ID=NUM_READS,Number=1,Type=Integer,Description="Total number of supporting read pairs, across all samples.')
		writer.write('\n##INFO=<ID=CMD,Number=1,Type=String,Description="Command used to generate file.')
		writer.write('\n##INFO=<ID=METHOD,Number=1,Type=String,Description="Software used to generate the file.')
		writer.write('\n##ALT=<ID=DEL,Description="Deletion">')
		writer.write('\n##ALT=<ID=INS,Description="Insertion">')
		writer.write('\n##ALT=<ID=INV,Description="Inversion">')
		writer.write('\n##ALT=<ID=ITX,Description="Intra-chromosomal translocation">')
		writer.write('\n##ALT=<ID=CTX,Description="Inter-chromosomal translocation">')
		writer.write('\n##ALT=<ID=Unknown,Description="Unknown">')
		writer.write('\n##FORMAT=<ID=NR,Number=1,Type=String,Description="Number of supporting read pairs from this sample">')
		writer.write('\n##FORMAT=<ID=SC,Number=1,Type=String,Description="Score">')
		vcf_fields = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'FORMAT']
		vcf_fields = vcf_fields + samples
		writer.write('\n#%s\n' % '\t'.join(vcf_fields))
		records = []
		ID = 0;
		for record in tsv:
			ID += 1
			CHROM = record['Chr1']
			POS = record['Pos1']
			ALT = '<%s>' % record['Type']
			INFO = 'ORIENTATION1=%s;CHR2=%s;POS2=%s;ORIENTATION2=%s;TYPE=%s;SIZE=%s;SCORE=%s;NUM_READS=%s;CMD=%s;METHOD=Breakdancer' % (
				record['Orientation1'],record['Chr2'],record['Pos2'],record['Orientation2'],record['Type'],record['Size'],record['Score'],record['num_Reads'], command[0])
			FORMAT = 'NR:SC'
			SAMPLES = []
			num_Reads_lib = record['num_Reads_lib'].split(':')
			reads_dict = {}
			for num_Reads in num_Reads_lib:
				pair = num_Reads.split('|')
				pair[0] = pair[0].split('/')[-1].split('.')[0]
				reads_dict.update({pair[0]:pair[1]})
			for sample in samples:
				if record[sample] is not None:
					SAMPLES.append('%s:%s' % (reads_dict[sample] if sample in reads_dict else '0',
						record[sample] if 'NA' not in record[sample] else '0'))
				else:
					SAMPLES.append('%s:%s' % (reads_dict[sample] if sample in reads_dict else '0','0'))
			records.append([CHROM, POS, '%s%08d' % (record['Type'], ID), '.', ALT, '.', '.', INFO, FORMAT, "\t".join(SAMPLES)])
		output = "\n".join(["\t".join(map(str, record)) for record in records])
		writer.write(output)

def parseOptions(argv):
	"""Parse the command line arguments for this script.
		Current arguments:
			-i: 				input tsv file
			--itsv:				input tsv file
		:param argv: the arguments string to be parsed
		:type argv: string
	"""
	try:
		opts, args = getopt.getopt(argv,"hi:",["itsv="])
	except getopt.GetoptError:
		print 'test.py -i <inputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'test.py -i <inputfile>'
			sys.exit()
		elif opt in ("-i", "--itsv"):
			files['itsv'] = arg

def main(argv):
	parseOptions(argv)
	files['ovcf'] = '%s.vcf' % files['itsv']
	print files['ovcf']
	parseTSV(genReaderDict())

if __name__ == "__main__":
	main(sys.argv[1:])
