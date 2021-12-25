"""User endpoints."""

import json
import requests
from flask import Blueprint, abort, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from myleagues_api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_DISCOVERY_URL,
)
from myleagues_api.models.access_token import AccessToken
from myleagues_api.models.league import League
from myleagues_api.models.user import User

blueprint_user = Blueprint("user", __name__)
CORS(blueprint_user)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@blueprint_user.route("/sso_login", methods=["POST"])
def sso_login():

    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = g.oauth_client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.host_url + "sso_callback",
        scope=["openid", "email", "profile"],
    )
    return request_uri


@blueprint_user.route("/sso_callback", methods=["GET"])
def sso_callback():

    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = g.oauth_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    g.oauth_client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = g.oauth_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    user_data = userinfo_response.json()

    return f"You are {user_data['name']}."


@blueprint_user.route("/user/login", methods=["POST"])
def login():
    """Create endpoint for the 'login' action."""

    data = request.json

    try:

        user = User.get_by_email_and_password(
            email=data["email"], password=data["password"]
        )

    except HTTPException as e:
        if e.code in [403, 404]:
            abort(403, "Invalid credentials")

        raise e

    return jsonify({"access_token": AccessToken.generate_and_store(user)}), 200


@blueprint_user.route("/user/register", methods=["POST"])
def register():
    """Create endpoint for the 'register' action."""

    data = request.json

    user = User.create(
        username=data["username"],
        email=data["email"],
        password=data["password"],
    )

    return jsonify({"access_token": AccessToken.generate_and_store(user)}), 200


@blueprint_user.route("/user/join_league", methods=["POST"])
def join_league():
    """Create endpoint for the 'join league' action."""

    data = request.json

    User().add_to_league(user_id=g.user_id, league_id=data["league_id"])

    league = League.read_one({"id": data["league_id"]})

    return (
        jsonify(
            {
                "data": {
                    "type": "leagues",
                    "id": str(league.id),
                    "attributes": {
                        **league.as_dict(),
                        "ranking": league.get_ranking(),
                        "players": league.get_players(),
                        "matches": league.get_matches(),
                    },
                }
            }
        ),
        200,
    )


@blueprint_user.route("/user/leagues", methods=["GET"])
def user_leagues():
    """Create endpoint for the 'get leagues for user' action."""

    user = User.read({"id": g.user_id})

    data = []
    for league in user.leagues:
        data.append(
            {
                "type": "leagues",
                "id": str(league.id),
                "attributes": {
                    **league.as_dict(),
                    "ranking": league.get_ranking(),
                    "players": league.get_players(),
                    "matches": league.get_matches(),
                },
            }
        )

    return jsonify({"data": data}), 200
