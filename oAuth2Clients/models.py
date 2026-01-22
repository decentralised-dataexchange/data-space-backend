"""
OAuth2 Clients Models Module

This module defines OAuth 2.0 client models for the data space platform.
OAuth2 clients enable organisations to authenticate and authorize access to
the platform's APIs and resources using standard OAuth 2.0 flows.

Two client models are provided:
- OAuth2Clients: Internal clients for accessing platform services
- OrganisationOAuth2Clients: Client credentials for organisation-specific integrations

These clients support the Client Credentials flow commonly used in B2B/M2M scenarios.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from django.db import models

from organisation.models import Organisation


class OAuth2Clients(models.Model):
    """
    Represents an OAuth 2.0 client for platform API access.

    This model stores OAuth 2.0 client credentials that organisations use to
    authenticate with the data space platform APIs. Clients are used in the
    Client Credentials grant type, which is appropriate for machine-to-machine
    communication where no user interaction is required.

    Each organisation can create multiple clients to segregate access for
    different applications, environments (dev/staging/prod), or purposes.

    Security Considerations:
        - Client secrets should be treated as sensitive credentials
        - Secrets are auto-generated if not provided during creation
        - Consider implementing secret rotation policies
        - Inactive clients should have is_active set to False

    Relationships:
        - Many-to-One with Organisation: Each client belongs to one organisation

    Constraints:
        - client_id must be unique across all clients
        - (organisation, name) must be unique - each org's client names are distinct
    """

    # Unique identifier for this client record in the database
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    # OAuth 2.0 client identifier
    # Used in authentication requests to identify the client application
    # Auto-generated in format "client_<12-char-hex>" if not provided
    # Indexed for fast lookup during token validation
    client_id: models.CharField[str, str] = models.CharField(
        max_length=255, unique=True, db_index=True
    )

    # OAuth 2.0 client secret
    # Used together with client_id for client authentication
    # Auto-generated in format "secret_<24-char-hex>" if not provided
    # Should be stored securely and transmitted only over HTTPS
    client_secret: models.CharField[str, str] = models.CharField(max_length=255)

    # Human-readable name for the client
    # Helps organisation admins identify and manage their clients
    # Must be unique within each organisation
    name: models.CharField[str, str] = models.CharField(
        max_length=255, help_text="Human-readable name for the client"
    )

    # Optional description providing additional context about the client
    # Useful for documenting the client's purpose, environment, or contact info
    description: models.TextField[str, str] = models.TextField(
        blank=True, help_text="Optional description of the client"
    )

    # Reference to the organisation that owns this client
    # All API access using this client is attributed to this organisation
    organisation: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="oauth_clients"
    )

    # Flag indicating whether the client is active and can authenticate
    # Set to False to immediately revoke access without deleting the client
    # Useful for temporary suspension or incident response
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    # Timestamp when the client was created
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp of the most recent update to this client
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "oauth2_clients"
        verbose_name = "OAuth2 Client"
        verbose_name_plural = "OAuth2 Clients"
        # Order by newest first for admin listings
        ordering = ["-created_at"]
        constraints = [
            # Ensure each organisation can only have one client with a given name
            models.UniqueConstraint(
                fields=["organisation", "name"], name="uniq_organisation_client_name"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.client_id}) - {self.organisation.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to auto-generate client_id and client_secret if not provided.

        The generated credentials follow a predictable format:
        - client_id: "client_" + 12 random hex characters
        - client_secret: "secret_" + 24 random hex characters

        These can be overridden by explicitly setting the fields before saving.
        """
        # Generate client_id and client_secret if not provided
        if not self.client_id:
            self.client_id = f"client_{uuid.uuid4().hex[:12]}"
        if not self.client_secret:
            self.client_secret = f"secret_{uuid.uuid4().hex[:24]}"
        super().save(*args, **kwargs)


class OrganisationOAuth2Clients(models.Model):
    """
    Represents an OAuth 2.0 client for organisation-specific API integrations.

    This model is similar to OAuth2Clients but serves a different purpose - it
    stores client credentials that organisations configure for their own use cases,
    potentially for accessing external services or for custom integrations.

    The distinction allows the platform to separate:
    - Platform-managed clients (OAuth2Clients): For accessing data space APIs
    - Organisation-managed clients (OrganisationOAuth2Clients): For custom integrations

    Security Considerations:
        - Same security practices as OAuth2Clients apply
        - Organisations are responsible for managing these credentials
        - Consider implementing audit logging for credential usage

    Relationships:
        - Many-to-One with Organisation: Each client belongs to one organisation

    Constraints:
        - client_id must be unique across all organisation clients
        - (organisation, name) must be unique within this model
    """

    # Unique identifier for this client record in the database
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    # OAuth 2.0 client identifier for this integration
    # Unique across all organisation OAuth clients
    # Indexed for efficient lookup during authentication
    client_id: models.CharField[str, str] = models.CharField(
        max_length=255, unique=True, db_index=True
    )

    # OAuth 2.0 client secret for authentication
    # Paired with client_id for the Client Credentials flow
    client_secret: models.CharField[str, str] = models.CharField(max_length=255)

    # Human-readable name identifying this client
    # Helps organisation admins manage their integrations
    name: models.CharField[str, str] = models.CharField(
        max_length=255, help_text="Human-readable name for the client"
    )

    # Optional description for additional documentation
    # Can include integration details, responsible team, etc.
    description: models.TextField[str, str] = models.TextField(
        blank=True, help_text="Optional description of the client"
    )

    # Reference to the owning organisation
    # API operations and audits are attributed to this organisation
    organisation: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="organisation_oauth_clients",
    )

    # Flag to enable/disable the client without deletion
    # Provides quick access revocation capability
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    # Timestamp when the client was created
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp of the most recent modification
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "organisation_oauth2_clients"
        verbose_name = "Organisation OAuth2 Client"
        verbose_name_plural = "Organisation OAuth2 Clients"
        # Order by newest first
        ordering = ["-created_at"]
        constraints = [
            # Ensure unique client names within each organisation
            models.UniqueConstraint(
                fields=["organisation", "name"], name="uniq_client_name"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.client_id}) - {self.organisation.name}"
