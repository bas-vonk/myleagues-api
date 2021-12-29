import json
import os
import random

import requests
from werkzeug.exceptions import HTTPException

from myleagues_api.models.access_token import AccessToken
from myleagues_api.models.saml_providers.saml_provider import BaseSamlProvider
from myleagues_api.models.user import User

GOOGLE_PROVIDER_NAME = "google"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


class SamlProviderGoogle(BaseSamlProvider):
    """Class for the Google SAML provider."""

    def __init__(self):
        super().__init__(GOOGLE_PROVIDER_NAME, GOOGLE_CLIENT_ID)

    @staticmethod
    def get_provider_cfg():
        """Get the provider config."""
        return requests.get(GOOGLE_DISCOVERY_URL).json()

    def get_request_uri(self):
        """Get the request URI."""

        # Find out what Authorization endpoint to hit for Google SSO
        provider_cfg = self.get_provider_cfg()
        authorization_endpoint = provider_cfg["authorization_endpoint"]

        # Create the state parameter
        state = self.create_state_parameter(self.provider_name)

        # Prepare and return the request uri
        return self.oauth_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=self.get_redirect_uri(),
            scope=["openid", "email", "profile"],
            state=state,
        )

    def callback(self, code, request_url):
        """Process the callback."""

        # Find out what token endpoint to hit for Google SSO
        provider_cfg = self.get_provider_cfg()
        token_endpoint = provider_cfg["token_endpoint"]

        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = self.oauth_client.prepare_token_request(
            token_endpoint,
            authorization_response=request_url,
            redirect_url=self.get_redirect_uri(),
            code=code,
        )

        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        self.oauth_client.parse_request_body_response(json.dumps(token_response.json()))

        # Now that you have tokens (yay) let's find and hit the URL
        # from Google that gives you the user's profile information,
        # including their Google profile picture and email
        userinfo_endpoint = provider_cfg["userinfo_endpoint"]
        uri, headers, body = self.oauth_client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        user_data = userinfo_response.json()

        # Check if user exists with the given email address

        try:
            user = User().read({"google_sub": user_data["sub"]})

            # Update picture and locale
            user.picture = user_data["picture"]
            user.locale = user_data["locale"]

            user.save()

        except HTTPException:

            # Generate unique username
            username_base = user_data["email"].split("@")[0]
            username_candidate = username_base
            suffix = 1

            print(username_candidate)
            print(User().username_exists(username_candidate))
            # print("doei")

            while User().username_exists(username_candidate):
                username_candidate = username_base + str(suffix)
                suffix = suffix + 1

            user = User.create(
                username=username_candidate,
                password=random.choice(["apple", "banana", "citrus"]),
                picture=user_data["picture"],
                locale=user_data["locale"],
                google_sub=user_data["sub"],
            )

        # Generate an access token and return it
        return AccessToken.generate_and_store(user)
