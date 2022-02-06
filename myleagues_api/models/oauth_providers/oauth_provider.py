import json
import os
import time
from abc import ABC, abstractmethod

from cryptography.fernet import Fernet
from flask import abort
from oauthlib.oauth2 import WebApplicationClient

ENCODING = "utf-8"

state_validity_seconds = 300

f = Fernet(os.environ["FERNET_KEY"].encode(ENCODING))


class BaseOAuthProvider(ABC):
    """Base class for the OAuth providers."""

    def __init__(self, provider_name, client_id):

        self.provider_name = provider_name
        self.oauth_client = WebApplicationClient(client_id)

    @staticmethod
    def get_redirect_uri():
        """Return the redirect URI for this app."""
        return os.environ["OAUTH_REDIRECT_URI"]

    @abstractmethod
    def get_request_uri(self):
        """Expose 'Get request uri' endpoint."""
        raise NotImplementedError(
            "Child class must implement 'get_request_uri' method."
        )

    @abstractmethod
    def callback(self):
        """Expose the 'callback' endpoint."""
        raise NotImplementedError("Child class must implement 'callback' method.")

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
