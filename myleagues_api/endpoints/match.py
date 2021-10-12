"""User endpoints."""
from datetime import datetime
from time import time

from flask import Blueprint, abort, g, jsonify, request
from flask_cors import CORS

from myleagues_api.models.match import Match

blueprint_match = Blueprint("match", __name__)
CORS(blueprint_match)


@blueprint_match.route("/match", methods=["POST"])
def post():
    """Create endpoint for the 'create match' action."""

    data = request.json

    # Store a match
    match = Match.create(
        league_id=data["league_id"],
        date=datetime.strptime(data["date"], "%Y-%m-%d"),
        home_player_id=data["home_player_id"],
        home_score=data["home_score"],
        away_player_id=data["away_player_id"],
        away_score=data["away_score"],
        created_by=g.user_id,
        created_at=time(),
    )

    return (
        jsonify(
            {
                "data": {
                    "type": "matches",
                    "id": str(match.id),
                    "attributes": {
                        "id": match.id,
                        "date": match.date,
                        "home_player_username": match.home_player.username,
                        "away_player_username": match.away_player.username,
                        "home_score": match.home_score,
                        "away_score": match.away_score,
                    },
                }
            }
        ),
        200,
    )
