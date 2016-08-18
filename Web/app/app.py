from flask import Flask
from maps import Maps
import MySQLdb

variants = MySQLdb.connect("localhost", "root", "12345", "DogSVStore")
variants_cursor = variants.cursor()
maps = Maps(variants, variants_cursor, 1)
maps.gen_dicts()

queries = MySQLdb.connect("localhost", "root", "12345", "Library")
queries_cursor = queries.cursor()

app = Flask(__name__)
app.config.from_object('config')
