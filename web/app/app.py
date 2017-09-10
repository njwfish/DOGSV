import MySQLdb
from flask import Flask

from QueryJSON import QueryJSONEncoder, QueryJSONDecoder
from maps import Maps

variants = MySQLdb.connect("localhost", "root", "", "dogsv")
variants_cursor = variants.cursor()
maps = Maps(variants, variants_cursor, 1)
maps.gen_dicts()

queries = MySQLdb.connect("localhost", "root", "", "library")
queries_cursor = queries.cursor()

app = Flask(__name__)
app.config.from_object('config')
app.json_encoder = QueryJSONEncoder
app.json_decoder = QueryJSONDecoder
