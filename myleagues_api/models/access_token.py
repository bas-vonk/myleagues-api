import uuid
from os import environ
from time import time
from typing import Dict, Union

import jwt
from flask import abort
from myleagues_api.db import db
from myleagues_api.models.user import User
from sqlalchemy.dialects.postgresql import UUID

ISSUER = "myleagues-api"
ALGORITHM = "RS256"
LIFE_SPAN = 86400  # 24 hours

PRIVATE_KEY = environ["PRIVATE_KEY"]
PUBLIC_KEY = environ["PUBLIC_KEY"]


class AccessToken(db.Model):
    """The Access Token class."""

    __tablename__ = "access_tokens"

    # fmt: off
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), index=True, unique=False)
    access_token = db.Column(db.Text)
    created_at = db.Column(db.BigInteger, index=False)
    # fmt: on

    @classmethod
    def generate_and_store(cls, user: User) -> str:
        """Generate and store an access token."""

        payload = {
            "iss": ISSUER,
            "exp": time() + LIFE_SPAN,
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
        }
        access_token_string = jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)
        access_token_object = cls(
            user_id=user.id, access_token=access_token_string, created_at=time()
        )

        db.session.add(access_token_object)

        return access_token_string

    @staticmethod
    def verify_and_return_contents(access_token: str) -> Dict[str, Union[int, str]]:
        """Verify and returns the contents of an access token.

        Parameters
        ----------
        access_token : str
            Access token.

        Returns
        -------
        Dict[str, Union[int, str]]
            Dictionary with the contents of the access (JWT) token.

        """

        try:

            decoded_token = jwt.decode(
                access_token.encode(), PUBLIC_KEY, issuer=ISSUER, algorithms=[ALGORITHM]
            )
            return decoded_token

        except (
            jwt.exceptions.InvalidTokenError,
            jwt.exceptions.InvalidSignatureError,
            jwt.exceptions.InvalidIssuerError,
            jwt.exceptions.ExpiredSignatureError,
        ):

            abort(401, "Access token invalid.")