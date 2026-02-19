"""
Connection Views Module

This module provides API endpoints for managing DISP (Data Intermediary Service Provider)
connections between data sources and the data marketplace digital wallet. These connections
enable secure communication channels for data exchange operations.

Business Context:
- Connections are established between a Data Source (organisation) and mobile wallet users
- Each connection uses DIDComm protocol for secure, decentralized communication
- Firebase dynamic links are generated for easy mobile app deep-linking
"""

from __future__ import annotations

from typing import Any

import requests
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.views import APIView

from dataspace_backend.settings import DATA_MARKETPLACE_APIKEY, DATA_MARKETPLACE_DW_URL
from dataspace_backend.utils import get_datasource_or_400, paginate_queryset

from .models import Connection
from .serializers import DISPConnectionSerializer


class DISPConnectionView(APIView):
    """
    API View for creating new DISP connections.

    Business Purpose:
        Enables a Data Source to create a new connection invitation that can be
        shared with mobile wallet users. This is the first step in establishing
        a secure communication channel for data exchange.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Data Source

    Workflow:
        1. Validates the requesting user has an associated Data Source
        2. Calls the digital wallet API to create a connection invitation
        3. Generates a Firebase dynamic link for mobile deep-linking
        4. Stores the connection record in pending 'invitation' state
        5. Returns connection details and invitation URLs
    """

    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Create a new connection invitation.

        Business Logic:
            Creates a single-use, auto-accepting connection invitation via the
            digital wallet API. The invitation can be shared as a URL or QR code.

        Request:
            POST /connections/
            No body required

        Response (200 OK):
            {
                "connection": {
                    "connectionId": str,
                    "invitation": {
                        "@type": str,
                        "@id": str,
                        "serviceEndpoint": str,
                        "label": str,
                        "imageUrl": str,
                        "recipientKeys": list
                    },
                    "invitationUrl": str
                },
                "firebaseDynamicLink": str
            }

        Error Responses:
            - 400: Data source not found or digital wallet API error

        Business Rules:
            - Connection is created with 'invitation' state initially
            - Multi-use is disabled (single recipient per invitation)
            - Auto-accept is enabled for seamless user experience
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        # Call digital wallet to create connection
        url = f"{DATA_MARKETPLACE_DW_URL}/v2/connections/create-invitation?multi_use=false&auto_accept=true"
        authorization_header = DATA_MARKETPLACE_APIKEY

        try:
            response = requests.post(
                url, headers={"Authorization": authorization_header}, timeout=30
            )
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.RequestException as e:
            return JsonResponse(
                {"error": f"Error calling digital wallet: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        connection_id = response.get("connection_id")

        url = f"{DATA_MARKETPLACE_DW_URL}/v1/connections/{connection_id}/invitation/firebase"
        try:
            create_firebase_dynamic_link_response = requests.post(
                url, headers={"Authorization": authorization_header}, timeout=30
            )
            create_firebase_dynamic_link_response.raise_for_status()
            create_firebase_dynamic_link_response = (
                create_firebase_dynamic_link_response.json()
            )
        except requests.exceptions.RequestException as e:
            return JsonResponse(
                {"error": f"Error creating Firebase dynamic link: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        firebase_dynamic_link = create_firebase_dynamic_link_response.get(
            "firebase_dynamic_link"
        )

        # Create a connection record without deleting any active connections
        Connection.objects.create(
            dataSourceId=datasource,
            connectionId=connection_id,
            connectionState="invitation",
            connectionRecord={},
        )

        connection_response_data = {
            "connectionId": connection_id,
            "invitation": {
                "@type": response.get("invitation", {}).get("@type"),
                "@id": response.get("invitation", {}).get("@id"),
                "serviceEndpoint": response.get("invitation", {}).get(
                    "serviceEndpoint"
                ),
                "label": response.get("invitation", {}).get("label"),
                "imageUrl": response.get("invitation", {}).get("imageUrl"),
                "recipientKeys": response.get("invitation", {}).get("recipientKeys"),
            },
            "invitationUrl": response.get("invitation_url"),
        }

        create_connection_response = {
            "connection": connection_response_data,
            "firebaseDynamicLink": firebase_dynamic_link,
        }

        return JsonResponse(create_connection_response)


class DISPConnectionsView(APIView):
    """
    API View for listing all active DISP connections.

    Business Purpose:
        Provides a paginated list of all active connections for a Data Source.
        This allows administrators to monitor and manage their established
        connections with mobile wallet users.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Data Source

    Business Rules:
        - Only returns connections in 'active' state
        - Connections in other states (invitation, inactive) are filtered out
        - Results are paginated for performance
    """

    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all active connections for the authenticated Data Source.

        Business Logic:
            Retrieves all connections that have been successfully established
            (state='active') for the requesting Data Source.

        Request:
            GET /connections/
            Query Parameters:
                - page (int): Page number for pagination
                - limit (int): Number of items per page

        Response (200 OK):
            {
                "connections": [
                    {
                        "id": str,
                        "connectionId": str,
                        "connectionState": str,
                        "dataSourceId": str,
                        ...
                    }
                ],
                "pagination": {
                    "currentPage": int,
                    "totalItems": int,
                    "totalPages": int,
                    "limit": int,
                    "hasPrevious": bool,
                    "hasNext": bool
                }
            }

        Error Responses:
            - 400: Data source not found
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        connection_data: list[Any] = []
        pagination_data: dict[str, Any] = {}
        try:
            connections_qs = Connection.objects.filter(
                dataSourceId=datasource, connectionState="active"
            )
            paginated_connections, pagination_data = paginate_queryset(
                connections_qs, request
            )
            serializer = DISPConnectionSerializer(paginated_connections, many=True)
            connection_data = list(serializer.data)

        except Connection.DoesNotExist:
            # If no connection exists, return empty data
            connection_data = []
            pagination_data = {
                "currentPage": 0,
                "totalItems": 0,
                "totalPages": 0,
                "limit": 0,
                "hasPrevious": False,
                "hasNext": False,
            }

        # Construct the response data
        response_data = {"connections": connection_data, "pagination": pagination_data}

        return JsonResponse(response_data)


class DISPDeleteConnectionView(APIView):
    """
    API View for deleting a specific DISP connection.

    Business Purpose:
        Allows a Data Source to terminate an existing connection. This is used
        when a connection is no longer needed or when cleaning up stale connections.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Data Source

    Business Rules:
        - Only connections belonging to the authenticated user's Data Source can be deleted
        - Deletion is permanent and cannot be undone
        - The connection must exist before it can be deleted
    """

    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(
        self, request: Request, connectionId: str, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """
        Delete a specific connection by its ID.

        Business Logic:
            Permanently removes a connection from the system. The connection
            must belong to the authenticated user's Data Source.

        Request:
            DELETE /connections/{connectionId}/

        Path Parameters:
            - connectionId (str): UUID of the connection to delete

        Response:
            - 204 No Content: Connection successfully deleted
            - 400: Connection not found or doesn't belong to the Data Source

        Business Rules:
            - Connection ownership is verified before deletion
            - No cascade effects on other entities
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        try:
            connection = Connection.objects.get(
                pk=connectionId, dataSourceId=datasource
            )
            connection.delete()
            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        except Connection.DoesNotExist:
            # If no connection exists, return error
            return JsonResponse(
                {"error": "Data source connection not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
