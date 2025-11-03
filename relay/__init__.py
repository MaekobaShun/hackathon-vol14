from flask import Flask

app = Flask(__name__)
import relay.main

from relay import db
db.create_table()