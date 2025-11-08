import os
from flask import Flask
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
import relay.main

from relay import db
db.create_table()