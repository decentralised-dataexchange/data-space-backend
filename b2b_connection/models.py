"""
B2B Connection Models Module

This module defines the Business-to-Business (B2B) connection model for the
data space platform. B2B connections represent established communication channels
between organisations, enabling secure, authenticated data exchange through
the data space infrastructure.

B2B connections are essential for organizations that need to exchange data
directly with each other under the governance of Data Disclosure Agreements.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from organisation.models import Organisation


class B2BConnection(models.Model):
    """
    Represents a Business-to-Business connection between organisations.

    A B2B Connection is a secure communication channel established between
    two organisations within the data space. Unlike user-level connections,
    B2B connections operate at the organisation level and are used for
    automated, machine-to-machine data exchange.

    These connections are typically established as part of the Data Disclosure
    Agreement workflow. When an organisation subscribes to another organisation's
    DDA and both parties complete the handshake, a B2B connection is created
    to facilitate data transfer.

    The connection can leverage various protocols including:
    - DIDComm for secure, encrypted messaging
    - OAuth2/OpenID Connect for API authentication
    - Custom protocols as defined by the data space governance

    Relationships:
        - Many-to-One with Organisation: Each connection belongs to one organisation
          (the local party in the connection)

    Business Rules:
        - Each B2B connection has a unique b2bConnectionId for reference
        - The full connection record preserves protocol-specific details
        - Connections should be established only between verified organisations
        - Deletion of an organisation cascades to its B2B connections
    """

    class Meta:
        verbose_name = "B2B Connection"
        verbose_name_plural = "B2B Connection"

    # Unique identifier for this B2B connection record in the database
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Reference to the organisation that owns/initiated this connection
    # This is the local party in the B2B relationship
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )

    # Complete JSON record of the B2B connection details
    # Contains protocol-specific information such as:
    # - Remote organisation identifier
    # - Connection endpoints
    # - Authentication/encryption keys
    # - Protocol version and capabilities
    b2bConnectionRecord: JSONField[Any, Any] = JSONField()

    # Unique identifier for this connection across the system
    # Used in API calls and for correlation with external systems
    # Format may vary based on the underlying protocol (e.g., DID, UUID)
    b2bConnectionId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )

    # Timestamp when the B2B connection was established
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp of the most recent activity or update on this connection
    # Can be used to track connection health and activity
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)
