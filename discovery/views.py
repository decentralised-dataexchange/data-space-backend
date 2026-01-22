"""
Discovery module for the Data Marketplace.

This module implements well-known configuration endpoints that enable
automatic service discovery for data marketplace participants. These
endpoints follow standard conventions for OAuth 2.0 and data space
discovery protocols.
"""

from typing import Any

from constance import config
from django.http import HttpRequest, JsonResponse
from django.views import View


class DataMarketPlaceConfigurationView(View):
    """
    Data Space configuration discovery endpoint.

    This endpoint provides the well-known configuration for the Data Marketplace,
    enabling clients to automatically discover service endpoints and capabilities.
    It follows data space interoperability standards for service discovery.

    Business Context:
        In a federated data space ecosystem, participants need to discover
        available services dynamically. This endpoint provides the necessary
        metadata for clients to locate the data space endpoint, authorization
        servers, and notification endpoints without hardcoding URLs.

    Authentication:
        No authentication required. This is a public discovery endpoint.

    Response Format (200 OK):
        {
            "data_space_endpoint": "https://...",
            "authorization_servers": ["https://..."],
            "notification_endpoint": "https://..."
        }

    Use Cases:
        - Initial setup of data marketplace clients
        - Dynamic service discovery in multi-tenant deployments
        - Federation with other data spaces
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Return the Data Marketplace configuration metadata.

        Business Logic:
            Constructs and returns the discovery document containing:
            - data_space_endpoint: Main API endpoint for data space operations
            - authorization_servers: List of OAuth 2.0 authorization server URLs
            - notification_endpoint: Endpoint for receiving async notifications

        All URLs are dynamically constructed from the configured BASE_URL,
        allowing the same codebase to work across different deployments.

        Returns:
            JsonResponse with the configuration metadata.
        """
        base_url = config.BASE_URL
        data_space_endpoint = f"{base_url}/service"
        authorization_server = f"{base_url}/service"
        notification_endpoint = f"{base_url}/service/notification"
        configuration = {
            "data_space_endpoint": data_space_endpoint,
            "authorization_servers": [authorization_server],
            "notification_endpoint": notification_endpoint,
        }

        return JsonResponse(configuration)


class DataMarketPlaceAuthorizationConfigurationView(View):
    """
    OAuth 2.0 Authorization Server metadata endpoint.

    This endpoint provides the OAuth 2.0 authorization server metadata
    following RFC 8414 (OAuth 2.0 Authorization Server Metadata). It enables
    clients to discover the authorization server configuration.

    Business Context:
        For secure machine-to-machine communication in the data marketplace,
        clients need to know where to obtain access tokens. This endpoint
        provides the necessary OAuth 2.0 metadata for clients to configure
        their authentication automatically.

    Authentication:
        No authentication required. This is a public discovery endpoint
        (typically served at /.well-known/oauth-authorization-server).

    Response Format (200 OK):
        {
            "issuer": "https://...",
            "token_endpoint": "https://..."
        }

    Standards Compliance:
        - RFC 8414: OAuth 2.0 Authorization Server Metadata
        - OAuth 2.0 client_credentials grant support
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Return the OAuth 2.0 authorization server metadata.

        Business Logic:
            Constructs and returns the authorization server metadata containing:
            - issuer: The authorization server's issuer identifier
            - token_endpoint: URL for obtaining access tokens

        This information allows OAuth 2.0 clients to automatically configure
        themselves to authenticate with this authorization server.

        Returns:
            JsonResponse with the authorization server metadata.
        """
        base_url = config.BASE_URL
        issuer = f"{base_url}/service"
        token_endpoint = f"{base_url}/service/token"
        configuration = {"issuer": issuer, "token_endpoint": token_endpoint}

        return JsonResponse(configuration)
