import random
import string
import uuid
from time import time

from flask import abort
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from myleagues_api.db import db
from myleagues_api.models.ranking_systems.ranking import RankingSystemFactory
from myleagues_api.models.ranking_systems.ranking_perron_frobenius import (
    PerronFrobeniusRankingSystem,
)
from myleagues_api.models.ranking_systems.ranking_regular import RegularRankingSystem
from myleagues_api.tables.participations import participations

# Register the ranking systems
# TODO: Would be nice to do this in the individual files, but this causes
# a problem where the ranking systems are not registered because the files are not
# loaded
ranking_system_factory = RankingSystemFactory()
ranking_system_factory.register_ranking_system("regular", RegularRankingSystem)
ranking_system_factory.register_ranking_system(
    "perron_frobenius", PerronFrobeniusRankingSystem
)


class League(db.Model):
    """League model."""

    __tablename__ = "leagues"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(32))
    ranking_system = db.Column(db.String(32))
    join_code = db.Column(db.String(4), index=True, unique=True)
    admin_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.BigInteger, index=False)
    deleted_at = db.Column(db.BigInteger, index=False)

    players = db.relationship(
        "User",
        secondary=participations,
        order_by="asc(User.id)",
        backref="league",
        lazy=True,
    )
    matches = db.relationship(
        "Match",
        order_by="asc(Match.date), asc(Match.created_at)",
        backref="league",
        lazy=True,
    )

    @classmethod
    def create(cls, name, admin_user_id, ranking_system="regular"):
        """Create a league."""

        # Check if the ranking system exists
        if ranking_system not in ranking_system_factory._ranking_systems:
            abort(404, "Ranking system not found.")

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
        """Read one league from the database."""

        try:
            return cls.query.filter_by(**filter).one()
        except NoResultFound:
            abort(404, "No league found.")
        except MultipleResultsFound:
            abort(409, "Multiple leagues found. Define stricter filters.")

    @classmethod
    def read_many(cls, filter):
        """Read many leagues from the database."""

        if "player_id" in filter:
            return cls.query.join(participations).filter(
                participations.columns.user_id == filter["player_id"]
            )

        return cls.query.filter_by(**filter).all()

    def get_ranking(self):
        """Get the current ranking for this league."""

        ranking_system = ranking_system_factory.get_ranking_system(
            self.ranking_system, league=self
        )
        return ranking_system.get_ranking()

    def get_ranking_history(self):
        """Get the ranking history for this league."""

        ranking_system = ranking_system_factory.get_ranking_system(
            self.ranking_system, league=self
        )
        return ranking_system.get_ranking_history()

    def get_players(self):
        """Get the players for this league."""

        players = []
        for player in self.players:
            players.append({"id": player.id, "username": player.username})

        return players

    def get_matches(self):
        """Get the matches for this league."""

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
        """Set the join code."""

        self.join_code = self.get_unique_join_code()

    def as_dict(self):
        """Return the league as dictionary."""

        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    @classmethod
    def get_unique_join_code(cls, length=4):
        """Get a unique join code."""

        join_code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=length)
        )

        if not cls.query.filter_by(join_code=join_code).first():
            return join_code
        else:
            return cls.get_unique_join_code()
