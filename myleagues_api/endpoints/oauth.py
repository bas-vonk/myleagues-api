"""SSO endpoints."""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from myleagues_api.models.oauth_providers.oauth_provider import (
    BaseOAuthProvider,
    OAuthProviderFactory,
)
from myleagues_api.models.oauth_providers.oauth_provider_google import (
    OAuthProviderGoogle,
)
from myleagues_api.models.oauth_providers.oauth_provider_microsoft import (
    OAuthProviderMicrosoft,
)


# Register the OAuth providers
# TODO: Would be nice to do this in the individual files, but this causes a problem
# where the ranking systems are not registered because the files are not loaded
oauth_provider_factory = OAuthProviderFactory()
oauth_provider_factory.register_oauth_provider("google", OAuthProviderGoogle)
oauth_provider_factory.register_oauth_provider("microsoft", OAuthProviderMicrosoft)

blueprint_oauth = Blueprint("oauth", __name__)
CORS(blueprint_oauth)


@blueprint_oauth.route("/oauth/get_request_uri/<provider_name>", methods=["GET"])
def get_request_uri(provider_name):
    """Expose 'Get request URI' endpoint."""

    # Get the provider
    oauth_provider = oauth_provider_factory.get_oauth_provider(provider_name)

    request_uri = oauth_provider.get_request_uri()

    return jsonify({"request_uri": request_uri})


@blueprint_oauth.route("/oauth/callback", methods=["GET"])
def callback():
    """Expose 'Callback' endpoint."""

    # Get authorization code Google sent back to you
    code = request.args.get("code")
    state = request.args.get("state")

    # First parse the state to find out what the provider is
    state_dict = BaseOAuthProvider.validate_state_parameter_and_return_contents(state)

    # Get the provider
    oauth_provider = oauth_provider_factory.get_oauth_provider(state_dict["provider"])

    # Process the callback (which returns a myleagues access token)
    access_token = oauth_provider.callback(code, request.url)

    return jsonify({"access_token": access_token}), 200
