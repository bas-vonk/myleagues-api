"""Match model."""

import uuid

from sqlalchemy.dialects.postgresql import UUID

from myleagues_api.db import db


class Match(db.Model):

    __tablename__ = "matches"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    league_id = db.Column(UUID(as_uuid=True), db.ForeignKey("leagues.id"), index=True)
    date = db.Column(db.Date, index=False)
    home_player_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), index=True
    )
    home_score = db.Column(db.Integer, index=False)
    away_player_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("users.id"), index=True
    )
    away_score = db.Column(db.Integer, index=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.BigInteger, index=False)
    approved_at = db.Column(db.BigInteger, index=False, nullable=True)
    rejected_at = db.Column(db.BigInteger, index=False, nullable=True)
    deleted_at = db.Column(db.BigInteger, index=False, nullable=True)

    home_player = db.relationship(
        "User", backref="match_home_player", foreign_keys=home_player_id, lazy=True
    )
    away_player = db.relationship(
        "User", backref="match_away_player", foreign_keys=away_player_id, lazy=True
    )

    @classmethod
    def create(
        cls,
        league_id,
        date,
        home_player_id,
        home_score,
        away_player_id,
        away_score,
        created_by,
        created_at,
    ):

        match = cls(
            league_id=league_id,
            date=date,
            home_player_id=home_player_id,
            home_score=home_score,
            away_player_id=away_player_id,
            away_score=away_score,
            created_by=created_by,
            created_at=created_at,
        )

        db.session.add(match)
        db.session.commit()
        db.session.refresh(match)

        return match

    def as_dict(self):

        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
