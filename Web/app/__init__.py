from flask import Flask
import MySQLdb
from maps import Maps

app = Flask(__name__)
app.config.from_object('config')

variants = MySQLdb.connect("localhost","root","12345","DogSVStore" )
variants_cursor = variants.cursor()
maps = Maps(variants, variants_cursor)
maps.genDicts()

queries = MySQLdb.connect("localhost","root","12345","Library" )
queries_cursor = queries.cursor()

from app import views