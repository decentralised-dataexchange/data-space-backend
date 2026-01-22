"""
Connection Models Module

This module defines the Connection model for tracking peer-to-peer connections
in the data space ecosystem. Connections are established between data sources
and data consumers using DIDComm protocols, enabling secure, authenticated
communication channels for data exchange.

Connections are a fundamental building block of the decentralized identity
infrastructure, allowing parties to establish trusted relationships before
engaging in data sharing activities.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from config.models import DataSource


class Connection(models.Model):
    """
    Represents a peer-to-peer connection between a data source and another party.

    In the context of decentralized identity and data exchange, a Connection
    represents an established DIDComm connection between two parties. This
    connection enables secure, encrypted communication and is typically a
    prerequisite for more complex interactions like credential issuance or
    data sharing.

    The connection lifecycle follows the DIDComm protocol:
    1. Invitation - One party creates a connection invitation
    2. Request - The other party sends a connection request
    3. Response - The inviter responds with connection details
    4. Complete - Both parties have established the connection

    Relationships:
        - Many-to-One with DataSource: Multiple connections per data source

    Business Rules:
        - Each connectionId must be unique across the system
        - Connection state tracks the DIDComm protocol state machine
        - Full connection record is preserved for audit and troubleshooting
    """

    # Unique identifier for this connection record in the local database
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Unique identifier for the connection from the DIDComm agent
    # This ID is used to reference the connection in API calls and webhook events
    # Indexed for fast lookups when processing connection-related events
    connectionId: models.CharField[str, str] = models.CharField(
        max_length=256, db_index=True, unique=True
    )

    # Current state of the connection in the DIDComm protocol
    # Common states: invitation, request, response, active, inactive, error
    # Used to track connection establishment progress and identify issues
    connectionState: models.CharField[str, str] = models.CharField(max_length=20)

    # Reference to the data source that owns this connection
    # The data source is the local party in this connection
    dataSourceId: models.ForeignKey[DataSource, DataSource] = models.ForeignKey(
        DataSource, on_delete=models.CASCADE
    )

    # Complete JSON record of the connection from the DIDComm agent
    # Contains DIDs, keys, endpoints, and other connection metadata
    # Preserved for debugging, auditing, and connection recovery
    connectionRecord: JSONField[Any, Any] = JSONField(max_length=512)

    def __str__(self) -> str:
        return str(self.connectionId)
