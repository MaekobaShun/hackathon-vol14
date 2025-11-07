import os
from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
import relay.main

from relay import db
db.create_table()