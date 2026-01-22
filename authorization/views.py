"""
Authorization module for the Data Marketplace.

This module implements the OAuth 2.0 authorization server functionality,
specifically the client_credentials grant type for machine-to-machine
authentication between data marketplace participants.
"""

import base64
from typing import Any

from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from oAuth2Clients.models import OAuth2Clients

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class DataMarketPlaceTokenView(APIView):
    """
    OAuth 2.0 Token endpoint implementing the client_credentials grant type.

    This endpoint serves as the authorization server for the Data Marketplace,
    allowing organisations to obtain JWT access tokens using their OAuth2
    client credentials. These tokens are used for authenticated API access
    in machine-to-machine scenarios.

    Business Context:
        The Data Marketplace uses OAuth 2.0 client_credentials flow for B2B
        integrations. Organisations register OAuth2 clients and use those
        credentials to obtain access tokens for automated data exchange
        operations without human intervention.

    Authentication:
        - HTTP Basic Authentication with client_id:client_secret
        - Authorization header: "Basic base64(client_id:client_secret)"
        - CSRF is disabled for this endpoint as it uses Basic Auth

    Request Format:
        Content-Type: application/x-www-form-urlencoded
        Body: grant_type=client_credentials

    Response Format (200 OK):
        {
            "access_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 3600
        }

    Security:
        - Only active OAuth2 clients can obtain tokens
        - Only active organisation admins can have tokens issued
        - Tokens are scoped to the organisation's permissions

    Errors:
        - 400: Invalid grant_type or content-type
        - 401: Invalid client credentials or inactive client/admin
        - 500: Server configuration error (missing admin)
    """

    permission_classes = [AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Issue a JWT access token for valid OAuth2 client credentials.

        Business Logic:
            1. Validates the request content-type (must be form-urlencoded)
            2. Validates grant_type (must be client_credentials)
            3. Extracts and validates Basic auth credentials
            4. Looks up the OAuth2 client and verifies it's active
            5. Retrieves the associated organisation's admin user
            6. Issues a JWT token for the admin user

        The issued token allows the client to perform API operations on
        behalf of the organisation, with permissions based on the admin user.

        Business Rules:
            - OAuth2 client must exist and be marked as active
            - Organisation must have an active admin user
            - Only client_credentials grant type is supported
            - Request must use application/x-www-form-urlencoded

        Returns:
            Response with access_token, token_type, and expires_in on success.
            Error response with error and error_description on failure.
        """
        # Extract grant_type from form or JSON
        grant_type = None
        if request.content_type == "application/json":
            return Response(
                {
                    "error": "invalid_request",
                    "error_description": "Content-Type must be application/x-www-form-urlencoded",
                }
            )
        if request.content_type != "application/x-www-form-urlencoded":
            return Response(
                {
                    "error": "invalid_request",
                    "error_description": "Missing required parameter: grant_type",
                }
            )

        grant_type = request.POST.get("grant_type")

        if grant_type != "client_credentials":
            return Response(
                {
                    "error": "unsupported_grant_type",
                    "error_description": "Only 'client_credentials' is supported",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse Basic auth header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Basic "):
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": "Missing Basic Authorization header",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            b64 = auth_header.split(" ", 1)[1].strip()
            decoded = base64.b64decode(b64).decode("utf-8")
            if ":" not in decoded:
                raise ValueError("Invalid basic auth format")
            client_id, client_secret = decoded.split(":", 1)
        except Exception:
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": "Invalid Basic Authorization header",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Find OAuth2 client and associated organisation
        try:
            oauth_client = OAuth2Clients.objects.select_related("organisation").get(
                client_id=client_id, client_secret=client_secret, is_active=True
            )
        except OAuth2Clients.DoesNotExist:
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": "Invalid client credentials",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        organisation = oauth_client.organisation
        try:
            admin_user = organisation.admin
        except Exception:
            return Response(
                {
                    "error": "server_error",
                    "error_description": "Organisation admin not found for this client",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        if not admin_user or not admin_user.is_active:
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": "Organisation admin is inactive or missing",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Issue JWT access token for organisation admin
        access = AccessToken.for_user(admin_user)
        expires_in = int(access.lifetime.total_seconds())

        response_data = {
            "access_token": str(access),
            "token_type": "Bearer",
            "expires_in": expires_in,
        }
        return Response(response_data, status=status.HTTP_200_OK)
