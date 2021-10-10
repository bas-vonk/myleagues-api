from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# This db instance can be be imported by anything (models, blueprint, the main app)
db = SQLAlchemy()


def init_db(app=None, db=None):
    """Initialize the global database object used by the app."""
    if isinstance(app, Flask) and isinstance(db, SQLAlchemy):

        db.init_app(app)

    else:
        raise ValueError("Cannot init DB without db and app objects.")
