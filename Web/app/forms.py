from flask_wtf import Form
from wtforms import SelectMultipleField, StringField, IntegerField, DecimalField, BooleanField, TextAreaField, validators

class BuilderForm(Form):
	chrom = StringField('chrom')
	chrom2 = StringField('chrom2')
	filter = StringField('filter')
	pos = IntegerField('pos', [validators.optional()])
	pos2 = IntegerField('pos2', [validators.optional()])
	len = IntegerField('len', [validators.optional()])
	DEL = BooleanField('DEL', default=False)
	DUP = BooleanField('DUP', default=False)
	INS = BooleanField('INS', default=False)
	INV = BooleanField('INV', default=False)
	TRA = BooleanField('TRA', default=False)
	SIN = BooleanField('SIN', default=False)
	LIN = BooleanField('LIN', default=False)
	BXP = BooleanField('BXP', default=False)

	homref = BooleanField('homref', default=False)
	het = BooleanField('het', default=False)
	homalt = BooleanField('HomAlt', default=False)

	breed_include = SelectMultipleField('breed_include',choices=[])
	breed_exclude = SelectMultipleField('breed_exclude',choices=[])

	sample_include = SelectMultipleField('individual_include',choices=[])
	sample_exclude = SelectMultipleField('individual_exclude',choices=[])
	tumor = BooleanField('tumor', default=False)

	tool_include = SelectMultipleField('tool_include',choices=[])
	tool_exclude = SelectMultipleField('tool_exclude',choices=[])

class QueryForm(Form):
	query = TextAreaField('query')

class SearchForm(Form):
	search = StringField('search')

class ColumnForm(Form):
	records_include= SelectMultipleField('records_include',choices=[])
	records_exclude= SelectMultipleField('records_exclude',choices=[])

	individuals_include= SelectMultipleField('individuals_include',choices=[])
	individuals_exclude= SelectMultipleField('individuals_exclude',choices=[])

	samples_include= SelectMultipleField('samples_include',choices=[])
	samples_exclude= SelectMultipleField('samples_exclude',choices=[])

	genotypes_include= SelectMultipleField('genotypes_include',choices=[])
	genotypes_exclude= SelectMultipleField('genotypes_exclude',choices=[])