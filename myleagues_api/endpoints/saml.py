"""SSO endpoints."""

from flask import Blueprint, jsonify, request
from flask_cors import CORS

from myleagues_api.models.saml_providers.saml_provider import (
    BaseSamlProvider,
    SamlProviderFactory,
)
from myleagues_api.models.saml_providers.saml_provider_google import SamlProviderGoogle

# Register the SAML providers
# TODO: Would be nice to do this in the individual files, but this causes a problem
# where the ranking systems are not registered because the files are not loaded
saml_provider_factory = SamlProviderFactory()
saml_provider_factory.register_saml_provider("google", SamlProviderGoogle)

blueprint_saml = Blueprint("saml", __name__)
CORS(blueprint_saml)


@blueprint_saml.route("/saml/get_request_uri/<provider_name>", methods=["GET"])
def get_request_uri(provider_name):
    """Expose 'Get request URI' endpoint."""

    # Get the provider
    saml_provider = saml_provider_factory.get_saml_provider(provider_name)

    request_uri = saml_provider.get_request_uri()

    return jsonify({"request_uri": request_uri})


@blueprint_saml.route("/saml/callback", methods=["GET"])
def callback():
    """Expose 'Callback' endpoint."""

    # Get authorization code Google sent back to you
    code = request.args.get("code")
    state = request.args.get("state")

    # First parse the state to find out what the provider is
    state_dict = BaseSamlProvider.validate_state_parameter_and_return_contents(state)

    # Get the provider
    saml_provider = saml_provider_factory.get_saml_provider(state_dict["provider"])

    # Process the callback (which returns a myleagues access token)
    access_token = saml_provider.callback(code, request.url)

    return jsonify({"access_token": access_token}), 200
