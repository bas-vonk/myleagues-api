"""League endpoints."""
from flask import Blueprint, abort, g, jsonify, request
from flask_cors import CORS

from myleagues_api.models.league import League
from myleagues_api.models.user import User


blueprint_league = Blueprint("league", __name__)
CORS(blueprint_league)


@blueprint_league.route("/league", methods=["POST"])
def create():
    """Create endpoint for 'create league' functionality."""

    data = request.json

    league = League.create(
        name=data["name"],
        ranking_system=data["ranking_system"],
        admin_user_id=g.user_id,
    )

    User().add_to_league(user_id=g.user_id, league_id=league.id)

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


@blueprint_league.route("/league/", defaults={"id": None})
@blueprint_league.route("/league/<id>", methods=["GET"])
def read(id):
    """Create endpoint for 'get league' functionality."""

    # Define the filters to find a league
    filter = {"id": id, "join_code": request.args.get("filter[join_code]")}
    filter = {key: value for key, value in filter.items() if value is not None}

    if len(filter.keys()) == 0:
        abort(400, "Invalid request. Pass at least one identifier.")

    if "id" in filter or "join_code" in filter:
        league = League.read_one(filter)
        data = {
            "type": "leagues",
            "id": str(league.id),
            "attributes": {
                **league.as_dict(),
                "ranking": league.get_ranking(),
                "players": league.get_players(),
                "matches": league.get_matches()[::-1],
            },
        }
    else:
        leagues = League.read_many(filter)
        data = []
        for league in leagues:
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

    return (
        jsonify({"data": data, "links": {"self": request.url}}),
        200,
    )


@blueprint_league.route("/league/<id>/ranking_history", methods=["GET"])
def get_ranking_history(id):
    """Create endpoint for 'get ranking history' functionality."""

    filter = {"id": id}

    league = League.read_one(filter)

    return (
        jsonify(
            {
                "data": {
                    "type": "leagues",
                    "id": str(league.id),
                    "attributes": {
                        **league.as_dict(),
                        "ranking_history": league.get_ranking_history(),
                    },
                }
            }
        ),
        200,
    )

    pass
