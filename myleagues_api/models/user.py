import hashlib
import os
import re
import uuid
from typing import Dict, Union

from cryptography.fernet import Fernet
from flask import abort
from myleagues_api.db import db
from myleagues_api.models.league import League
from myleagues_api.tables.participations import participations
from sqlalchemy import exc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.security import check_password_hash, generate_password_hash

# TODO: Replace with environment
ENCODING = "utf-8"

db_salt = os.environ["SECRET_KEY"]
f = Fernet(os.environ["FERNET_KEY"].encode(ENCODING))

HASH_METHOD = "pbkdf2:sha256:15000"

REGEX_KEY = r"Key\s\((.*)\)="

COLUMN_NAMES_HRF = {"email_hashed": "Email address", "username_hashed": "Username"}

COLUMNS_TO_HASH = ["username", "email"]
COLUMNS_TO_ENCRYPT = ["username", "email"]

SUFFIX_HASHED = "_hashed"
SUFFIX_ENCRYPTED = "_encrypted"


class User(db.Model):
    """The User class."""

    __tablename__ = "users"

    # fmt: off
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username_encrypted = db.Column(db.String(256))
    username_hashed = db.Column(db.String(128), unique=True)
    password_hashed = db.Column(db.String(128))
    email_encrypted = db.Column(db.String(256))
    email_hashed = db.Column(db.String(128), unique=True)
    email_confirmed_at = db.Column(db.DateTime, index=False)
    deleted_at = db.Column(db.BigInteger, index=False)

    leagues = db.relationship("League", secondary=participations, backref="user", lazy=True)
    # fmt: on

    @classmethod
    def create(cls, username, email, password):

        user_dict = {
            f"username{SUFFIX_ENCRYPTED}": cls.encrypt(username),
            f"username{SUFFIX_HASHED}": cls.hash(username),
            f"email{SUFFIX_ENCRYPTED}": cls.encrypt(email),
            f"email{SUFFIX_HASHED}": cls.hash(email),
            f"password{SUFFIX_HASHED}": generate_password_hash(password, HASH_METHOD),
        }

        user = cls(**user_dict)

        try:

            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

            return user

        except exc.IntegrityError as error:

            db.session.rollback()

            column_name = re.search(REGEX_KEY, str(error)).group(1)

            abort(409, f"{COLUMN_NAMES_HRF[column_name]} already taken.")

    @classmethod
    def read(cls, filter):

        try:
            return cls.query.filter_by(**filter).one()

        except NoResultFound:
            abort(404, "User not found.")

    @classmethod
    def get_by_email_and_password(
        cls, email: str, password: str
    ) -> Dict[str, Union["int, str"]]:
        """Get a user by email address and password."""

        # Hash the email to use that in the lookup
        user = cls.read({"email_hashed": cls.hash(email)})

        if not user.password_is_correct(password):
            abort(403, "Invalid password.")

        return user

    def password_is_correct(self, password: str) -> bool:
        return check_password_hash(self.password_hashed, password)

    @classmethod
    def add_to_league(cls, user_id, league_id):

        user = cls.read({"id": user_id})
        league = League.read_one(filter={"id": league_id})

        user.leagues.append(league)
        db.session.commit()

    @property
    def username(self):
        return self.decrypt(self.username_encrypted)

    @property
    def email(self):
        return self.decrypt(self.email_encrypted)

    @staticmethod
    def encrypt(value: str):
        return f.encrypt(value.encode(ENCODING)).decode(ENCODING)

    @staticmethod
    def decrypt(encrypted_value: str):
        return f.decrypt(encrypted_value.encode(ENCODING)).decode(ENCODING)

    @staticmethod
    def hash(value: str):

        # Assume no collisions will happen when using sha512
        # https://crypto.stackexchange.com/questions/89558/are-sha-256-and-sha-512-collision-resistant

        return hashlib.sha512(f"{db_salt}{value}".encode(ENCODING)).hexdigest()

    # def as_dict(self):
    #
    #     user = {
    #         column.name: getattr(self, column.name) for column in self.__table__.columns
    #     }
    #
    #     # Drop hashed values
    #     user = {k: v for k, v in user.items() if not k.endswith(SUFFIX_HASHED)}
    #
    #     # Add decrypted values
    #     user = {
    #         k.replace(SUFFIX_ENCRYPTED, ""): self.decrypt(v)
    #         for k, v in user.items()
    #         if k.endswith(SUFFIX_ENCRYPTED)
    #     }
    #
    #     # Drop decrypted values
    #     user = {k: v for k, v in user.items() if not k.endswith(SUFFIX_ENCRYPTED)}
    #
    #     return user


if __name__ == "__main__":
    print(User())
