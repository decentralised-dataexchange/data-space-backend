"""
Authorization Serializers.

This module provides serializers for OAuth2 authorization flows,
specifically implementing the client_credentials grant type used
for machine-to-machine (M2M) authentication.

The serializers handle token request validation and response
formatting according to OAuth2 specifications (RFC 6749).
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers


class TokenRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Serializer for validating OAuth2 token requests.

    Implements validation for the client_credentials grant type,
    which is used for server-to-server authentication where no
    user context is required. The client authenticates using
    its client_id and client_secret to obtain an access token.

    Supported grant types:
    - client_credentials: Machine-to-machine authentication
    """

    # Client identifier issued during OAuth2 client registration
    client_id = serializers.CharField(max_length=255)

    # Client secret for authenticating the client (should be kept confidential)
    client_secret = serializers.CharField(max_length=255)

    # OAuth2 grant type - only client_credentials is currently supported
    grant_type = serializers.CharField(max_length=50)

    def validate_grant_type(self, value: str) -> str:
        """
        Validate that the requested grant type is supported.

        Currently only the 'client_credentials' grant type is implemented,
        which is appropriate for M2M authentication scenarios in the
        data space where services need to authenticate without user
        intervention.

        Args:
            value: The grant_type value from the token request.

        Returns:
            The validated grant_type value.

        Raises:
            ValidationError: If the grant_type is not 'client_credentials'.
        """
        if value != "client_credentials":
            raise serializers.ValidationError(
                "Only 'client_credentials' grant type is supported"
            )
        return value


class TokenResponseSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Serializer for formatting OAuth2 token responses.

    Structures the token response according to OAuth2 specification
    (RFC 6749 Section 5.1), providing the access token and associated
    metadata required by clients to make authenticated API requests.
    """

    # The issued access token (typically a JWT) for authenticating API requests
    access_token = serializers.CharField()

    # Token type indicator - always "Bearer" for this implementation,
    # indicating the token should be sent in the Authorization header
    token_type = serializers.CharField(default="Bearer")

    # Token validity duration in seconds; clients should refresh
    # or request a new token before this expires
    expires_in = serializers.IntegerField()

    # Space-delimited list of granted scopes; empty if no specific
    # scopes were requested or if default scopes apply
    scope = serializers.CharField(default="", allow_blank=True)
