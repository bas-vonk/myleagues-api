"""WSGI module."""

from myleagues_api import create_app
from myleagues_api.db import db

if __name__ == "__main__":

    # Create app
    app = create_app(config_file="configs/postgresql.py", db=db)

    # Run the app
    app.run(host="0.0.0.0", port=80, debug=True, ssl_context="adhoc")
