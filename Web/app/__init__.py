from flask import Flask
import MySQLdb

app = Flask(__name__)
app.config.from_object('config')

db = MySQLdb.connect("localhost","root","12345","DogSVStore" )
cursor = db.cursor()

from app import views