"""User endpoints."""

from flask import Blueprint, abort, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from myleagues_api.models.access_token import AccessToken
from myleagues_api.models.league import League
from myleagues_api.models.user import User

blueprint_user = Blueprint("user", __name__)
CORS(blueprint_user)


@blueprint_user.route("/user/login", methods=["POST"])
def login():
    """Create endpoint for the 'login' action."""

    data = request.json

    try:

        user = User.get_by_username_and_password(
            username=data["username"], password=data["password"]
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
