from flask_wtf import Form
from wtforms import StringField, IntegerField, DecimalField, BooleanField
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