"""
Serializers for managing connections in the Data Space platform.

This module provides serializers for:
- DIDComm connections between the Data Intermediary Service Provider (DISP)
  and data sources

Connections represent established DIDComm communication channels between
entities in the data space. These connections enable secure, authenticated
messaging for credential exchange and data sharing operations.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import Connection


class DISPConnectionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for DISP (Data Intermediary Service Provider) connections.

    Represents a DIDComm connection between the DISP and a data source.
    These connections are established through the DIDComm protocol and
    are used for secure communication during credential presentations
    and data exchange operations.

    Fields:
        id: Unique identifier for this connection record (internal)
        connectionId: The DIDComm connection identifier (external protocol ID)
        connectionState: Current state of the connection (e.g., invitation,
                        request, active, completed)
        dataSourceId: Reference to the data source on the other end
        connectionRecord: Full connection record data (JSON) containing
                         DIDComm protocol details, DIDs, and metadata
    """

    class Meta:
        model = Connection
        fields = [
            "id",
            "connectionId",
            "connectionState",
            "dataSourceId",
            "connectionRecord",
        ]
