from app import app
from Blueprints.index import index
from Blueprints.results import results
from Blueprints.build import build
from Blueprints.builder import builder
from Blueprints.query import query
from Blueprints.library import library
from Blueprints.sql_to_vcf import sql_to_vcf
from Blueprints.process import process

app.register_blueprint(index)
app.register_blueprint(results)
app.register_blueprint(build)
app.register_blueprint(builder)
app.register_blueprint(query)
app.register_blueprint(library)
app.register_blueprint(sql_to_vcf)
app.register_blueprint(process)