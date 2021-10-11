"""Join table."""

from sqlalchemy.dialects.postgresql import UUID

from myleagues_api.db import db

participations = db.Table(
    "participations",
    db.Column(
        "league_id", UUID(as_uuid=True), db.ForeignKey("leagues.id"), primary_key=True
    ),
    db.Column(
        "user_id", UUID(as_uuid=True), db.ForeignKey("users.id"), primary_key=True
    ),
)
