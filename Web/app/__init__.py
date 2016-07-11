from flask import Flask
import MySQLdb
from maps import Maps

app = Flask(__name__)
app.config.from_object('config')

db = MySQLdb.connect("localhost","root","12345","DogSVStore" )
cursor = db.cursor()
maps = Maps(db, cursor)
maps.genDicts()

from app import views