import os
import uuid
import base64

import requests
from werkzeug.exceptions import HTTPException

from myleagues_api.models.oauth_providers.oauth_provider import BaseOAuthProvider
from myleagues_api.models.user import User

GOOGLE_PROVIDER_NAME = "google"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


class OAuthProviderGoogle(BaseOAuthProvider):
    """Class for the Google OAuth provider."""

    def __init__(self):
        super().__init__(
            GOOGLE_PROVIDER_NAME,
            GOOGLE_CLIENT_ID,
            GOOGLE_CLIENT_SECRET,
            GOOGLE_DISCOVERY_URL,
        )

    def _get_picture_uri(self, user_data):

        # Prepare the call to obtain the image by adding the access_token
        uri, headers, body = self.oauth_client.add_token(user_data["picture"])

        # Obtain the image
        response = requests.get(uri, headers=headers, data=body)

        return (
            f"data:{response.headers['Content-Type']};"
            f"base64,{base64.b64encode(response.content).decode('utf-8')}"
        )

    @staticmethod
    def _get_username_from_email_address(email_address):

        # Generate unique username
        username_base = email_address.split("@")[0]
        username = username_base
        suffix = 1

        while User().username_exists(username):
            username = username_base + str(suffix)
            suffix = suffix + 1

        return username

    def process_user_data(self, user_data):

        # First check if a user already exists for this Google identity
        # If it exists, update the 'locale' and 'picture' and return the user
        try:

            # Scenario A: User already exists

            user = User().read({"google_sub": user_data["sub"]})

            user.locale = user_data["locale"]
            user.picture = self._get_picture_uri(user_data)
            user.save()

            return user

        except HTTPException:

            # Scenario B: User not found --> Create new user

            # Obtain a unique username
            username = self._get_username_from_email_address(user_data["email_address"])

            # Create the user
            return User.create(
                username=username,
                password=uuid.uuid4().hex,
                picture=self._get_picture_uri(),
                google_sub=user_data["sub"],
            )
