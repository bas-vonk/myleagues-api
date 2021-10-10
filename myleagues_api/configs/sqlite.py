from datetime import timedelta
from os import environ

# SQLAlchemy configurations
SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask configurations
SECRET_KEY = environ["SECRET_KEY"]
PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
TESTING = True
