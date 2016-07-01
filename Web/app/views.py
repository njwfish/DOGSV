from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',title='Home')

@app.route('/results')
def results():
    return render_template('index.html',title='Home')