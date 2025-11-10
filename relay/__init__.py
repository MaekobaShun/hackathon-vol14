import os

import cloudinary
from flask import Flask

app = Flask(__name__)

secret_key = (
    os.environ.get('SECRET_KEY')
    or os.environ.get('FLASK_SECRET_KEY')
    or os.urandom(24)
)
app.secret_key = secret_key

cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
cloud_api_key = os.environ.get('CLOUDINARY_API_KEY')
cloud_api_secret = os.environ.get('CLOUDINARY_API_SECRET')

default_upload_dir = os.path.join(app.root_path, 'static', 'uploads')


if cloud_name and cloud_api_key and cloud_api_secret:
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=cloud_api_key,
        api_secret=cloud_api_secret,
        secure=True,
    )
    app.config['USE_CLOUDINARY'] = True
else:
    app.config['USE_CLOUDINARY'] = False

    uploads_env = os.environ.get('UPLOAD_FOLDER')
    uploads_dir = os.path.abspath(uploads_env) if uploads_env else default_upload_dir
    os.makedirs(uploads_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = uploads_dir

from relay import db  # noqa: E402

db.create_table()

import relay.main  # noqa: E402