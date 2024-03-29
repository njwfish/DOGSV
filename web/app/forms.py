from flask_wtf import FlaskForm as Form
from wtforms import SelectMultipleField, StringField, IntegerField, BooleanField, TextAreaField, validators


class BuilderForm(Form):
    ref = StringField('ref')
    alt = StringField('alt')
    qual = StringField('qual')
    filter = StringField('filter')
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

    region_include = SelectMultipleField('region_include', choices=[])
    region_exclude = SelectMultipleField('region_exclude', choices=[])

    breed_include = SelectMultipleField('breed_include', choices=[])
    breed_exclude = SelectMultipleField('breed_exclude', choices=[])

    sample_include = SelectMultipleField('individual_include', choices=[])
    sample_exclude = SelectMultipleField('individual_exclude', choices=[])
    tumor = BooleanField('tumor', default=False)

    tool_include = SelectMultipleField('tool_include', choices=[])
    tool_exclude = SelectMultipleField('tool_exclude', choices=[])

    tool_clauses = SelectMultipleField('tool_clauses', choices=[])


class QueryForm(Form):
    input_query = TextAreaField('input_query')


class SearchForm(Form):
    search = StringField('search')


class ColumnForm(Form):
    columns_include = SelectMultipleField('columns_include', choices=[])
    columns_exclude = SelectMultipleField('columns_exclude', choices=[])
