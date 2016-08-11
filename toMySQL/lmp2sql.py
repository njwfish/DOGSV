#!/usr/bin/python

import sys
import glob, os
from VCFtoMySQL_Loader import VCFtoMySQL

CHROM_format = 'chr'
hasGT = True

'''TODO: Change tool_id value to the ID of the correct tool'''
ids = {
    'individual_id': 	'0',
    'variant_id':		'0',
    'tool_id': 			'LMP',
}

'''TODO: Add variant types specific to this tool on the left,
        and the type (one of the seven listed below) it is equivalent to
        on the right. Do not delete any of the current fields.'''
variant_type_mapping = {
    'DEL': 'DEL',
    'DUP': 'DUP',
    'INS': 'INS',
    'INV': 'INV',
    'TRA': 'TRA',
    'SIN': 'SIN',
    'LIN': 'LIN',
    'BXP': 'BXP',
    'DUP:TANDEM': 'DUP',
    'CNV': 'BXP',
    'BND': 'BXP'
}

'''TODO: Change the right side of the values to be updated to the correct
        corresponding fields. Use @info is it is in the INFO secion, and
        @samples if it is in the SAMPLES section.
        Likely the only fields that will change are CHROM2, POS2, and LEN.
        If there are no corresponding fields, delete the whole line. For
        example, if there is no LEN corollary in this VCF, then dont leave
        'LEN': '', simply delete that line from the declaration.'''
core = {
    'CHROM':	'CHROM',
    'POS': 		'POS',
    'REF': 		'REF',
    'ALT': 		'ALT',
    'QUAL': 	'QUAL',
    'FILTER': 	'FILTER',
    'TYPE':		'SVTYPE @info',
    'CHROM2': 	'CHR2 @info',
    'POS2': 	'END @info',
    'LEN': 		'LEN @info'
}

'''TODO: Replace and extend all these placeholder values with the actual fields
        from the INFO section of the VCF. Anything not added will not go into
        the database.'''
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

'''TODO: Replace and extend all these placeholder values with the actual fields
        from the SAMPLES section of the VCF. Anything not added will not go into
        the database.'''
toolSamples = [
    'SU',
    'PE',
    'SR',
    'BD'
]


def main(argv):
    vcf_loader = VCFtoMySQL(ids, variant_type_mapping, core, toolInfo, toolSamples, CHROM_format, hasGT)
    for file in glob.glob("*.vcf"):
        vcf_loader.load(file)

if __name__ == "__main__":
    main(sys.argv[1:])