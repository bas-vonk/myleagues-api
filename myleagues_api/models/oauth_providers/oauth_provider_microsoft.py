import os
import uuid
import base64

import requests
from werkzeug.exceptions import HTTPException

from myleagues_api.models.oauth_providers.oauth_provider import BaseOAuthProvider
from myleagues_api.models.oauth_providers.default_avatar import DEFAULT_AVATAR
from myleagues_api.models.user import User

MICROSOFT_PROVIDER_NAME = "microsoft"
MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID", None)
MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET", None)
MICROSOFT_DISCOVERY_URL = (
    "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
)

DEFAULT_LOCALE = "en"


class OAuthProviderMicrosoft(BaseOAuthProvider):
    """Class for the Microsoft OAuth provider."""

    def __init__(self):
        super().__init__(
            MICROSOFT_PROVIDER_NAME,
            MICROSOFT_CLIENT_ID,
            MICROSOFT_CLIENT_SECRET,
            MICROSOFT_DISCOVERY_URL,
        )

    def _get_picture_uri(self, user_data):

        # Prepare the call to obtain the image by adding the access_token
        uri, headers, body = self.oauth_client.add_token(user_data["picture"])

        # Obtain the image
        response = requests.get(uri, headers=headers, data=body)

        # Fallback for if the response is not an image
        if response.headers["Content-Type"] == "application/json":
            return DEFAULT_AVATAR

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

            user = User().read({"microsoft_sub": user_data["sub"]})

            user.locale = DEFAULT_LOCALE
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
                microsoft_sub=user_data["sub"],
            )
