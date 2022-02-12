import json
import os
import time
from abc import ABC, abstractmethod


import requests
from cryptography.fernet import Fernet
from flask import abort
from oauthlib.oauth2 import WebApplicationClient

from myleagues_api.models.access_token import AccessToken


ENCODING = "utf-8"

state_validity_seconds = 300

f = Fernet(os.environ["FERNET_KEY"].encode(ENCODING))


class BaseOAuthProvider(ABC):
    """Base class for the OAuth providers."""

    def __init__(self, provider_name, client_id, client_secret, discovery_url):

        self.provider_name = provider_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.discovery_url = discovery_url

        self.oauth_client = WebApplicationClient(self.client_id)

    @property
    def redirect_uri(self):
        """Return the redirect URI for this app."""
        return os.environ["OAUTH_REDIRECT_URI"]

    def get_provider_cfg(self):
        """Get the provider config."""
        return requests.get(self.discovery_url).json()

    def get_request_uri(self):
        """Get the request URI."""

        # Find out what Authorization endpoint to hit for Microsoft SSO
        provider_cfg = self.get_provider_cfg()
        authorization_endpoint = provider_cfg["authorization_endpoint"]

        # Create the state parameter
        state = self.create_state_parameter(self.provider_name)

        # Prepare and return the request uri
        return self.oauth_client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=self.redirect_uri,
            scope=["openid", "email", "profile"],
            state=state,
        )

    def _add_access_token_to_oauth_client(self, provider_cfg, code, request_url):

        # Prepare the request that will be sent later to obtain the access_token
        token_url, headers, body = self.oauth_client.prepare_token_request(
            provider_cfg["token_endpoint"],
            authorization_response=request_url,
            redirect_url=self.redirect_uri,
            code=code,
        )

        # Obtain the access_token
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(self.client_id, self.client_secret),
        )

        # Add the contents of the response of the call to fetch an access_token to
        # the oauth_client
        self.oauth_client.parse_request_body_response(json.dumps(token_response.json()))

    def _get_user_data_from_provider(self, provider_cfg):

        userinfo_endpoint = provider_cfg["userinfo_endpoint"]

        # Add the access token to the oauth_client for this specific endpoint
        uri, headers, body = self.oauth_client.add_token(userinfo_endpoint)

        # Obtain the user info and return it
        return requests.get(uri, headers=headers, data=body).json()

    @abstractmethod
    def process_user_data(self):
        raise NotImplementedError("Providers must define process_user_data function.")

    def callback(self, code, request_url):
        """Process the callback."""

        # Provider config contains relevant information for the OAuth provider
        provider_cfg = self.get_provider_cfg()

        # Obtain an access token and add it to oauth_client
        # (to be used when accessing the user profile)
        self._add_access_token_to_oauth_client(provider_cfg, code, request_url)

        # Get the basic information for the user
        user_data = self._get_user_data_from_provider(provider_cfg)

        # Process the data to either link to an existing user, or create one
        user = self.process_user_data(user_data)

        # Generate an access token and return it
        return AccessToken.generate_and_store(user)

    @staticmethod
    def create_state_parameter(provider_name):
        """Create state parameter."""
        state_str = json.dumps(
            {"provider": provider_name, "time_issued": int(time.time())}
        )
        return f.encrypt(state_str.encode(ENCODING)).decode(ENCODING)

    @staticmethod
    def validate_state_parameter_and_return_contents(state):
        """Validate state parameter and return contents."""

        state_dict = json.loads(f.decrypt(state.encode(ENCODING)).decode(ENCODING))

        # Check validity of state
        if time.time() - state_dict["time_issued"] > state_validity_seconds:
            abort(401, "State expired.")

        return state_dict


class OAuthProviderFactory:
    """Ranking system factory."""

    def __init__(self):
        self._oauth_providers = {}

    def register_oauth_provider(self, oauth_provider_name, oauth_provider_obj):
        """Register a OAuth provider."""

        self._oauth_providers[oauth_provider_name] = oauth_provider_obj

    def get_oauth_provider(self, oauth_provider_name, **kwargs):
        """Get a ranking system."""

        oauth_provider_obj = self._oauth_providers.get(oauth_provider_name)
        if not oauth_provider_obj:
            raise ValueError(oauth_provider_name)

        return oauth_provider_obj(**kwargs)
