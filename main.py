"""App Engine entrypoint."""

from myleagues_api import create_app
from myleagues_api.db import db

# Create app
app = create_app(config_file="configs/postgresql.py", db=db)
