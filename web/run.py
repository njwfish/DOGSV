#!flask/bin/python

import os, sys
print os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
app.run(debug=True)
