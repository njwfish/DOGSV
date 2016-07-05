from flask_wtf import Form
from wtforms import SelectMultipleField, StringField, IntegerField, DecimalField, BooleanField
from wtforms.validators import DataRequired

class RecordForm(Form):
	chrom = StringField('chrom')
	filt = StringField('filt')
	pos = IntegerField('pos')
	pos2 = IntegerField('pos2')
	length = IntegerField('length')
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

