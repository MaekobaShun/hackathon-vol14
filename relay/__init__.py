import os
from flask import Flask

app = Flask(__name__)

secret_key = (
    os.environ.get('SECRET_KEY')
    or os.environ.get('FLASK_SECRET_KEY')
    or os.urandom(24)
)
app.secret_key = secret_key

default_upload_dir = os.path.join(app.root_path, 'static', 'uploads')
uploads_dir = os.environ.get('UPLOAD_FOLDER', default_upload_dir)
os.makedirs(uploads_dir, exist_ok=True)
app.config['UPLOAD_FOLDER'] = uploads_dir

from relay import db  # noqa: E402
db.create_table()

import relay.main  # noqa: E402