import random
import string
import uuid
from time import time

from flask import abort
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from myleagues_api.db import db
from myleagues_api.models.ranking_systems.ranking_regular import Regular
from myleagues_api.models.ranking_systems.ranking_perron_frobenius import (
    PerronFrobenius,
)
from myleagues_api.tables.participations import participations


ranking_systems = {"regular": Regular, "perron_frobenius": PerronFrobenius}


class League(db.Model):

    __tablename__ = "leagues"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(32))
    ranking_system = db.Column(db.String(32))
    join_code = db.Column(db.String(4), index=True, unique=True)
    admin_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.BigInteger, index=False)
    deleted_at = db.Column(db.BigInteger, index=False)

    players = db.relationship(
        "User", secondary=participations, backref="league", lazy=True
    )
    matches = db.relationship(
        "Match", order_by="asc(Match.date)", backref="league", lazy=True
    )

    @classmethod
    def create(cls, name, admin_user_id, ranking_system="regular"):

        league = cls(
            name=name,
            admin_user_id=admin_user_id,
            ranking_system=ranking_system,
            created_at=time(),
        )
        league.set_join_code()

        db.session.add(league)
        db.session.commit()
        db.session.refresh(league)

        return league

    @classmethod
    def read_one(cls, filter):

        try:
            return cls.query.filter_by(**filter).one()
        except NoResultFound:
            abort(404, "No league found.")
        except MultipleResultsFound:
            abort(409, "Multiple leagues found. Define stricter filters.")

    @classmethod
    def read_many(cls, filter):

        if "player_id" in filter:
            return cls.query.join(participations).filter(
                participations.columns.user_id == filter["player_id"]
            )

        return cls.query.filter_by(**filter).all()

    def get_ranking(self):

        ranking_system = ranking_systems[self.ranking_system](league=self)
        return ranking_system.get_ranking()

    def get_ranking_history(self):
        ranking_system = ranking_systems[self.ranking_system](league=self)
        return ranking_system.get_ranking_history()

    def get_players(self):

        players = []
        for player in self.players:
            players.append({"id": player.id, "username": player.username})

        return players

    def get_matches(self):

        matches = []
        for match in self.matches:
            matches.append(
                {
                    "id": match.id,
                    "date": match.date,
                    "home_player_username": match.home_player.username,
                    "away_player_username": match.away_player.username,
                    "home_score": match.home_score,
                    "away_score": match.away_score,
                }
            )

        return matches

    def set_join_code(self):
        self.join_code = self.get_unique_join_code()

    def as_dict(self):

        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    @classmethod
    def get_unique_join_code(cls, length=4):

        join_code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=length)
        )

        if not cls.query.filter_by(join_code=join_code).first():
            return join_code
        else:
            return cls.get_unique_join_code()
