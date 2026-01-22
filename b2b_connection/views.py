"""
B2B Connection Views Module

This module provides API endpoints for managing Business-to-Business (B2B) connections
between organisations in the data space ecosystem. B2B connections represent the
established relationships between Data Sources and Data Using Services.

Business Context:
- B2B connections enable secure data exchange between organizations
- Connections are established after successful DDA signing and verification
- Each connection tracks the relationship state and associated metadata
- Connections are scoped to individual organisations for data isolation
"""

from typing import Any, cast

from django.db.models import QuerySet
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from b2b_connection.models import B2BConnection
from b2b_connection.serializers import B2BConnectionSerializer, B2BConnectionsSerializer
from dataspace_backend.utils import paginate_queryset
from organisation.models import Organisation


class B2BConnectionView(APIView):
    """
    API View for retrieving individual B2B connections.

    Business Purpose:
        Provides access to specific B2B connection details. B2B connections
        represent the established data sharing relationships between
        organisations that have completed the DDA signing process.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with an Organisation

    Business Rules:
        - Only connections belonging to the user's organisation are accessible
        - Connections are scoped to prevent cross-organisation access
        - Connection details include relationship metadata and state
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[B2BConnection]:
        """
        Filter B2B connections by the authenticated user's organisation.

        Business Logic:
            Ensures data isolation by only returning connections that belong
            to the requesting user's organisation. This prevents unauthorized
            access to other organisations' connection data.

        Returns:
            QuerySet of B2BConnection filtered by organisation,
            or empty QuerySet if organisation not found
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return B2BConnection.objects.filter(organisationId=organisation)
        except Organisation.DoesNotExist:
            return B2BConnection.objects.none()

    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Retrieve a specific B2B connection by its ID.

        Business Logic:
            Fetches the complete details of a specific B2B connection including
            its current state, associated organisations, and connection metadata.

        Request:
            GET /b2b-connections/{pk}/

        Path Parameters:
            - pk (str): Primary key of the B2B connection

        Response (200 OK):
            {
                "b2bConnection": {
                    "id": str,
                    "organisationId": str,
                    ... (connection details)
                }
            }

        Error Responses:
            - 404: Connection not found or access denied

        Business Rules:
            - Only the organisation's own connections are accessible
            - Returns complete connection details including metadata
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = B2BConnectionSerializer(client)
        response_data = {"b2bConnection": serializer.data}
        return JsonResponse(response_data)


class B2BConnectionsView(APIView):
    """
    API View for listing all B2B connections for an organisation.

    Business Purpose:
        Provides a paginated list of all B2B connections established by
        the authenticated user's organisation. This enables administrators
        to monitor and manage all their data sharing partnerships.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with an Organisation

    Business Rules:
        - Only connections belonging to the user's organisation are returned
        - Results are paginated for performance with large connection sets
        - Provides a comprehensive view of all data sharing relationships
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[B2BConnection]:
        """
        Filter B2B connections by the authenticated user's organisation.

        Business Logic:
            Ensures data isolation by only returning connections that belong
            to the requesting user's organisation.

        Returns:
            QuerySet of B2BConnection filtered by organisation,
            or empty QuerySet if organisation not found
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return B2BConnection.objects.filter(organisationId=organisation)
        except Organisation.DoesNotExist:
            return B2BConnection.objects.none()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all B2B connections for the authenticated organisation.

        Business Logic:
            Retrieves all B2B connections associated with the user's
            organisation with pagination support for scalability.

        Request:
            GET /b2b-connections/
            Query Parameters:
                - page (int): Page number for pagination
                - limit (int): Number of items per page

        Response (200 OK):
            {
                "b2bConnection": [
                    {
                        "id": str,
                        "organisationId": str,
                        ... (connection details)
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

        Business Rules:
            - Only organisation's own connections are included
            - Results are paginated for performance
            - Empty list returned if no connections exist
        """
        # List all clients
        clients = self.get_queryset()
        serializer = B2BConnectionsSerializer(clients, many=True)

        b2b_connections, pagination_data = paginate_queryset(
            cast(list[Any], serializer.data), request
        )
        response_data = {
            "b2bConnection": b2b_connections,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)
