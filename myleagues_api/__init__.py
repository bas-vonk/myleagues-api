"""App factory."""

from os import environ
from typing import Optional

from flask import Flask, Response, abort, g, jsonify, request
from flask_cors import CORS
from oauthlib.oauth2 import WebApplicationClient
from werkzeug.exceptions import HTTPException

from myleagues_api.config import GOOGLE_CLIENT_ID
from myleagues_api.db import init_db
from myleagues_api.endpoints.league import blueprint_league
from myleagues_api.endpoints.match import blueprint_match
from myleagues_api.endpoints.user import blueprint_user
from myleagues_api.models.access_token import AccessToken

OPEN_ENDPOINTS = ["user.login", "user.register", "user.sso_login", "user.sso_callback"]
OPEN_METHODS = ["OPTIONS"]


def add_before_request(app: Flask):
    """Add before_request function to app."""

    @app.before_request
    def before_request():
        """Run before each request.

        Check whether the access token is in the cookie in a proper way.
        If it isn't, redirect to the Login page.
        """

        # Add OAuth client
        g.oauth_client = WebApplicationClient(GOOGLE_CLIENT_ID)

        # There's a couple of open endpoints for which the user doesn't need to be
        # authenticated
        if request.endpoint in OPEN_ENDPOINTS or request.method in OPEN_METHODS:
            return

        # Parse and validate JWT token (authentication)
        auth_header = request.headers.get("Authorization")

        # Check if the Authorization header is present
        if not auth_header:
            abort(401, "Authorization header missing.")

        # Check if the token is presented as a 'Bearer' token
        if "Bearer" not in auth_header:
            abort(401, "No Bearer token found in the Authorization header.")

        # Validate and parse the token
        jwt_token_parsed = AccessToken.verify_and_return_contents(auth_header[7:])

        # Add user_id to global
        g.user_id = jwt_token_parsed["user_id"]


def add_errorhandler(app: Flask):
    """Add errorhandler to app."""

    @app.errorhandler(Exception)
    def errorhandler(e: HTTPException) -> Response:
        """Handle HTTPExceptions (thrown by flask.abort elsewhere in the software).

        Parameters
        ----------
        e : HTTPException
            The thrown exception.

        Returns
        -------
        Response
            Properly formatted response with the proper status code.

        """

        # Default code
        code: Optional[int] = 500
        description: Optional[str] = repr(e)
        if isinstance(e, HTTPException):
            code = e.code
            description = e.description

        return jsonify({"message": description}), code


def create_app(config_file, db) -> Flask:
    """Create the app."""

    app = Flask(__name__)

    with app.app_context():

        # Load configuration
        app.config.from_pyfile(config_file)

        # Echo all queries
        # app.config["SQLALCHEMY_ECHO"] = True

        # Allow Cross-Origin Resource Sharing headers
        CORS(app)

        # Initialize the database
        init_db(app, db)

        # Create the schema and make it the default schema
        db.engine.execute(f"CREATE SCHEMA IF NOT EXISTS {environ['POSTGRES_SCHEMA']}")
        db.engine.execute(f"SET search_path = {environ['POSTGRES_SCHEMA']}")

        # Create database, schema and tables
        db.create_all()
        db.session.commit()

        # Add before_request and errorhandler functions
        add_before_request(app)
        add_errorhandler(app)

        # Register all the blueprints (views/endpoints)
        app.register_blueprint(blueprint_user)
        app.register_blueprint(blueprint_league)
        app.register_blueprint(blueprint_match)

        # Return the app
        return app
