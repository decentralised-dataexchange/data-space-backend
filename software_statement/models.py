"""
Software Statement Models Module

This module defines models for managing software statements and their templates
in the data space platform. Software statements are verifiable credentials that
attest to the properties and capabilities of software applications (clients)
operating within the data space.

Software statements are commonly used in OAuth2/OpenID Connect Dynamic Client
Registration and in trust frameworks where client applications need to prove
their identity and authorization to access data services.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from django.db.models import JSONField

from organisation.models import Organisation


class SoftwareStatement(models.Model):
    """
    Represents a software statement credential for an organisation's application.

    A Software Statement is a verifiable credential that certifies the properties
    of a software application within the data space. It typically includes:
    - Client application identity and metadata
    - Authorized scopes and capabilities
    - Organizational affiliation
    - Compliance attestations

    Software statements are issued through a credential exchange process where
    the organisation's application receives a signed statement from a trusted
    authority (such as the data space operator).

    Use Cases:
        - Dynamic client registration with OAuth2 authorization servers
        - Proving client identity in B2B data exchange
        - Attestation of security and compliance properties

    Relationships:
        - Many-to-One with Organisation: Each software statement belongs to an organisation

    Business Rules:
        - Each credentialExchangeId must be unique (tracks the issuance process)
        - Status tracks the credential lifecycle (pending, issued, revoked, etc.)
        - Complete credential history is preserved for audit purposes
    """

    # Unique identifier for this software statement record
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Reference to the organisation that owns this software statement
    # The organisation's application is the subject of the credential
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )

    # Unique identifier for the credential exchange/issuance process
    # Used to track and correlate messages during credential issuance
    # Also serves as a reference when verifying or revoking the credential
    credentialExchangeId: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )

    # Current status of the software statement
    # Common states: pending, offer_sent, request_received, issued, revoked
    # Tracks the credential lifecycle from issuance to potential revocation
    status: models.CharField[str, str] = models.CharField(max_length=50)

    # Complete JSON record of the credential exchange history
    # Contains all messages and state transitions during issuance
    # Preserved for audit, debugging, and compliance verification
    credentialHistory: JSONField[Any, Any] = JSONField()

    # Timestamp when the software statement record was created
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp of the most recent update to this record
    # Updated when status changes or credential is refreshed
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)


class SoftwareStatementTemplate(models.Model):
    """
    Defines a template for software statement credential issuance.

    This model stores the configuration for issuing software statements
    within the data space. It references a credential definition that
    specifies the schema and attributes of the software statement credential.

    Templates are created by data space administrators to standardize
    the software statement format across all participating organisations.

    Use Cases:
        - Configuring what attributes are included in software statements
        - Linking to specific credential definitions in the verifiable
          credential infrastructure
        - Supporting multiple types of software statements for different
          use cases (e.g., public clients, confidential clients)

    Business Rules:
        - Templates reference credential definitions in the VC infrastructure
        - Multiple templates can exist for different software statement types
    """

    # Unique identifier for this template
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Human-readable name for this software statement template
    # Describes the type of software statement (e.g., "Confidential Client Statement")
    softwareStatementTemplateName: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )

    # Reference to the credential definition in the verifiable credential system
    # Defines the schema, attributes, and cryptographic properties of the credential
    # Format depends on the VC infrastructure (e.g., Aries, DIDComm)
    credentialDefinitionId: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    def __str__(self) -> str:
        return str(self.softwareStatementTemplateName)
