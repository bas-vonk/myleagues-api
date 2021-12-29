import uuid

from flask import abort
from sqlalchemy import exc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from myleagues_api.db import db
from myleagues_api.models.league import League
from myleagues_api.tables.participations import participations

HASH_METHOD = "pbkdf2:sha256:15000"


class User(db.Model):
    """The User class."""

    __tablename__ = "users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(256), unique=True)
    password_hashed = db.Column(db.String(128))
    picture = db.Column(db.String(256))
    locale = db.Column(db.String(2))
    google_sub = db.Column(db.String(128))
    deleted_at = db.Column(db.BigInteger, index=False)

    leagues = db.relationship(
        "League", secondary=participations, backref="user", lazy=True
    )

    @classmethod
    def save(cls):
        """Save the user."""

        db.session.commit()

        return cls

    @classmethod
    def create(cls, username, password, picture=None, locale=None, google_sub=None):
        """Create a user."""

        user_dict = {
            "username": username,
            "password_hashed": generate_password_hash(password, HASH_METHOD),
            "picture": picture,
            "locale": locale,
            "google_sub": google_sub,
        }

        user = cls(**user_dict)

        try:

            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

            return user

        except exc.IntegrityError:

            db.session.rollback()
            abort(409, f"Username already taken.")

    @classmethod
    def username_exists(cls, username: str):
        """Check whether a username exists."""

        # Catch the HTTP Exception thrown by Flask abort and return whether
        # a user exists or not
        try:
            cls.read({"username": username})
        except HTTPException:
            return False

        return True

    @classmethod
    def read(cls, filter):
        """Read a user."""

        try:
            return cls.query.filter_by(**filter).one()

        except NoResultFound:
            abort(404, "User not found.")

    @classmethod
    def get_by_username_and_password(cls, username: str, password: str):
        """Get a user by username and password."""

        # Get the user
        user = cls.read({"username": username})

        if not user.password_is_correct(password):
            abort(403, "Invalid password.")

        return user

    @classmethod
    def add_to_league(cls, user_id, league_id):
        """Add a player to a league."""

        user = cls.read({"id": user_id})
        league = League.read_one(filter={"id": league_id})

        user.leagues.append(league)
        db.session.commit()

    def password_is_correct(self, password: str) -> bool:
        """Check whether the password is correct."""

        return check_password_hash(self.password_hashed, password)
