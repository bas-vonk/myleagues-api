from os import environ

assert "POSTGRES_HOSTNAME" in environ, "POSTGRES_HOSTNAME missing from environment."
assert "POSTGRES_DATABASE" in environ, "POSTGRES_DATABASE missing from environment."
assert "POSTGRES_USERNAME" in environ, "POSTGRES_USERNAME missing from environment."
assert "POSTGRES_PASSWORD" in environ, "POSTGRES_PASSWORD missing from environment."

# SQLAlchemy configurations
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2"
    f"://{environ['POSTGRES_USERNAME']}:{environ['POSTGRES_PASSWORD']}"
    f"@{environ['POSTGRES_HOSTNAME']}/{environ['POSTGRES_DATABASE']}"
)

SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask configurations
SECRET_KEY = environ["SECRET_KEY"]
TESTING = False
