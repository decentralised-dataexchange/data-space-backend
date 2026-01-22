"""
B2B Connection Serializers.

This module provides serializers for Business-to-Business (B2B) connection
management. B2B connections represent trusted relationships between
organisations in the data space, enabling secure data exchange and
collaboration between business entities.

The serializers handle the conversion of B2BConnection model instances
to/from JSON representations for API operations.
"""

from rest_framework import serializers

from b2b_connection.models import B2BConnection


class B2BConnectionsSerializer(serializers.ModelSerializer[B2BConnection]):
    """
    Serializer for listing multiple B2B connections.

    Used for endpoints that return collections of B2B connections,
    such as listing all connections for an organisation. Exposes
    all fields from the B2BConnection model to provide complete
    connection information in list views.
    """

    class Meta:
        model = B2BConnection
        fields = "__all__"


class B2BConnectionSerializer(serializers.ModelSerializer[B2BConnection]):
    """
    Serializer for single B2B connection operations.

    Used for CRUD operations on individual B2B connection records,
    including creating new connections, retrieving connection details,
    updating connection status, and deleting connections. Exposes
    all fields from the B2BConnection model.
    """

    class Meta:
        model = B2BConnection
        fields = "__all__"
