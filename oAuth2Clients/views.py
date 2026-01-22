from typing import Any, cast

from django.db import IntegrityError
from django.db.models import QuerySet
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from dataspace_backend.utils import paginate_queryset
from organisation.models import Organisation

from .models import OAuth2Clients, OrganisationOAuth2Clients
from .serializers import (
    OAuth2ClientsCreateSerializer,
    OAuth2ClientsSerializer,
    OAuth2ClientsUpdateSerializer,
    OrganisationOAuth2ClientsCreateSerializer,
    OrganisationOAuth2ClientsSerializer,
)


class OAuth2ClientView(APIView):
    """
    API view for managing individual OAuth2 client credentials.

    This endpoint allows organisations to create, read, update, and delete
    their own OAuth2 client credentials used for machine-to-machine authentication
    in the data marketplace ecosystem.

    Business Context:
        OAuth2 clients enable programmatic access to the Data Marketplace API.
        Each organisation can have multiple OAuth2 clients for different
        applications or services that need to interact with the marketplace.

    Authentication:
        Requires JWT authentication. Only organisation administrators can
        manage OAuth2 clients for their own organisation.

    Security:
        - Clients are scoped to the authenticated user's organisation
        - Client names must be unique within an organisation
        - Client secrets are generated server-side and should be stored securely
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OAuth2Clients]:
        """
        Filter OAuth2 clients to only return those belonging to the authenticated
        user's organisation. This ensures data isolation between organisations.

        Returns:
            QuerySet of OAuth2Clients belonging to the user's organisation,
            or an empty QuerySet if the user is not an organisation admin.
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OAuth2Clients.objects.none()

    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Retrieve a specific OAuth2 client by its primary key.

        Business Logic:
            Returns the complete details of an OAuth2 client, including
            client_id and client_secret. This is typically used when an
            organisation admin needs to view or copy credentials for
            configuration purposes.

        Args:
            pk: The UUID primary key of the OAuth2 client to retrieve.

        Returns:
            JsonResponse containing the OAuth2 client details wrapped in
            {"oAuth2Client": {...}} structure.

        Raises:
            Http404: If the client does not exist or does not belong to
            the authenticated user's organisation.
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OAuth2ClientsSerializer(client)
        response_data = {"oAuth2Client": serializer.data}
        return JsonResponse(response_data)

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Create a new OAuth2 client for the authenticated user's organisation.

        Business Logic:
            Creates a new set of OAuth2 credentials (client_id, client_secret)
            that can be used for machine-to-machine authentication. The client
            is automatically associated with the organisation of the authenticated
            user.

        Request Format:
            {
                "name": "string (required, unique within organisation)",
                "description": "string (optional)"
            }

        Response Format (201 Created):
            {
                "oAuth2Client": {
                    "id": "uuid",
                    "name": "string",
                    "client_id": "string",
                    "client_secret": "string",
                    ...
                }
            }

        Business Rules:
            - Client name must be unique within the organisation
            - client_id and client_secret are auto-generated
            - Only organisation admins can create clients

        Errors:
            - 400: Validation errors or duplicate client name
        """
        serializer = OAuth2ClientsCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = self.request.user
            organisation = get_object_or_404(Organisation, admin=user)
            try:
                client = serializer.save(organisation=organisation)
            except IntegrityError:
                return JsonResponse(
                    {
                        "error": "duplicate_name",
                        "error_description": "Client name must be unique within the organisation",
                    },
                    status=400,
                )
            response_serializer = OAuth2ClientsSerializer(client)
            response_data = {"oAuth2Client": response_serializer.data}
            return JsonResponse(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(
        self, request: Request, pk: str, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Update an existing OAuth2 client's metadata.

        Business Logic:
            Allows updating the name and description of an OAuth2 client.
            Note that client_id and client_secret cannot be modified through
            this endpoint for security reasons.

        Args:
            pk: The UUID primary key of the OAuth2 client to update.

        Request Format:
            {
                "name": "string (optional, must be unique within organisation)",
                "description": "string (optional)"
            }

        Response Format (200 OK):
            {
                "oAuth2Client": {
                    "id": "uuid",
                    "name": "string",
                    ...
                }
            }

        Business Rules:
            - Only the client's metadata can be updated, not credentials
            - Name uniqueness constraint is enforced within the organisation
            - Client must belong to the authenticated user's organisation

        Errors:
            - 400: Validation errors or duplicate client name
            - 404: Client not found or not owned by user's organisation
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OAuth2ClientsUpdateSerializer(client, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return JsonResponse(
                    {
                        "error": "duplicate_name",
                        "error_description": "Client name must be unique within the organisation",
                    },
                    status=400,
                )
            response_serializer = OAuth2ClientsSerializer(client)
            response_data = {"oAuth2Client": response_serializer.data}
            return JsonResponse(response_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        """
        Permanently delete an OAuth2 client.

        Business Logic:
            Performs a hard delete of the OAuth2 client, immediately revoking
            any ability to authenticate using the associated credentials.
            This action is irreversible.

        Args:
            pk: The UUID primary key of the OAuth2 client to delete.

        Response:
            204 No Content on successful deletion.

        Business Rules:
            - Client must belong to the authenticated user's organisation
            - Deletion is permanent and cannot be undone
            - Any systems using these credentials will immediately lose access

        Security Considerations:
            - Used when credentials may have been compromised
            - Used when decommissioning an application or service
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OAuth2ClientsView(APIView):
    """
    API view for listing all OAuth2 clients belonging to an organisation.

    This endpoint provides a paginated list of all OAuth2 clients that have been
    created by the authenticated user's organisation.

    Business Context:
        Organisations may have multiple OAuth2 clients for different applications,
        environments (dev/staging/prod), or services. This endpoint allows
        administrators to view and manage all their credentials in one place.

    Authentication:
        Requires JWT authentication. Only the organisation administrator
        can view the list of clients.

    Response Format:
        {
            "oAuth2Clients": [...],
            "pagination": {
                "currentPage": int,
                "totalPages": int,
                "totalItems": int,
                "itemsPerPage": int
            }
        }
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OAuth2Clients]:
        """
        Filter OAuth2 clients to only return those belonging to the authenticated
        user's organisation.

        Returns:
            QuerySet of OAuth2Clients belonging to the user's organisation,
            or an empty QuerySet if the user is not an organisation admin.
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OAuth2Clients.objects.none()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all OAuth2 clients for the authenticated user's organisation.

        Business Logic:
            Returns a paginated list of all OAuth2 clients associated with
            the organisation. This is the primary endpoint for viewing all
            available credentials.

        Query Parameters:
            - page: Page number for pagination (default: 1)
            - pageSize: Number of items per page (default: system default)

        Response Format (200 OK):
            {
                "oAuth2Clients": [
                    {
                        "id": "uuid",
                        "name": "string",
                        "client_id": "string",
                        "client_secret": "string",
                        ...
                    },
                    ...
                ],
                "pagination": {...}
            }
        """
        clients = self.get_queryset()
        serializer = OAuth2ClientsSerializer(clients, many=True)

        oauth_clients, pagination_data = paginate_queryset(
            cast(list[Any], serializer.data), request
        )
        response_data = {
            "oAuth2Clients": oauth_clients,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


class OrganisationOAuth2ClientView(APIView):
    """
    API view for managing external OAuth2 client configurations.

    This endpoint allows organisations to store and manage OAuth2 credentials
    for external services (third-party APIs, partner systems, etc.) that the
    organisation needs to authenticate with.

    Business Context:
        Unlike OAuth2ClientView (which manages credentials FOR authentication TO
        this system), OrganisationOAuth2ClientView manages credentials that the
        organisation uses to authenticate WITH external systems. This enables
        secure storage of third-party API credentials used for data exchange.

    Authentication:
        Requires JWT authentication. Only organisation administrators can
        manage external OAuth2 client configurations.

    Use Cases:
        - Storing credentials for partner data marketplace connections
        - Managing API keys for external data sources
        - Configuring OAuth2 clients for B2B integrations

    Security:
        - Credentials are scoped to the authenticated user's organisation
        - Client names must be unique within an organisation
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OrganisationOAuth2Clients]:
        """
        Filter external OAuth2 client configurations to only return those
        belonging to the authenticated user's organisation.

        Returns:
            QuerySet of OrganisationOAuth2Clients belonging to the user's
            organisation, or an empty QuerySet if user is not an admin.
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OrganisationOAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OrganisationOAuth2Clients.objects.none()

    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Retrieve a specific external OAuth2 client configuration.

        Business Logic:
            Returns the complete details of an external OAuth2 client
            configuration, including stored credentials. Used when an
            organisation admin needs to view or update external service
            credentials.

        Args:
            pk: The UUID primary key of the external OAuth2 client to retrieve.

        Returns:
            JsonResponse containing the client configuration wrapped in
            {"organisationOAuth2Client": {...}} structure.

        Raises:
            Http404: If the client does not exist or does not belong to
            the authenticated user's organisation.
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OrganisationOAuth2ClientsSerializer(client)
        response_data = {"organisationOAuth2Client": serializer.data}
        return JsonResponse(response_data)

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Store a new external OAuth2 client configuration.

        Business Logic:
            Creates a new record to store OAuth2 credentials for an external
            service. Unlike internal OAuth2 clients, the credentials here are
            provided by the user (from the external service) rather than
            auto-generated.

        Request Format:
            {
                "name": "string (required, unique within organisation)",
                "client_id": "string (from external service)",
                "client_secret": "string (from external service)",
                "token_endpoint": "string (external service token URL)",
                ...
            }

        Response Format (201 Created):
            {
                "organisationOAuth2Client": {
                    "id": "uuid",
                    "name": "string",
                    ...
                }
            }

        Business Rules:
            - Client name must be unique within the organisation
            - Credentials should be obtained from the external service
            - Only organisation admins can create configurations

        Errors:
            - 400: Validation errors or duplicate client name
        """
        serializer = OrganisationOAuth2ClientsCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = self.request.user
            organisation = get_object_or_404(Organisation, admin=user)
            try:
                client = serializer.save(organisation=organisation)
            except IntegrityError:
                return JsonResponse(
                    {
                        "error": "duplicate_name",
                        "error_description": "Client name must be unique within the organisation",
                    },
                    status=400,
                )
            response_serializer = OrganisationOAuth2ClientsSerializer(client)
            response_data = {"organisationOAuth2Client": response_serializer.data}
            return JsonResponse(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(
        self, request: Request, pk: str, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Update an external OAuth2 client configuration.

        Business Logic:
            Allows updating all fields of an external OAuth2 client
            configuration, including credentials. This is used when external
            service credentials are rotated or endpoint URLs change.

        Args:
            pk: The UUID primary key of the external OAuth2 client to update.

        Request Format:
            {
                "name": "string (optional)",
                "client_id": "string (optional)",
                "client_secret": "string (optional)",
                "token_endpoint": "string (optional)",
                ...
            }

        Response Format (200 OK):
            {
                "organisationOAuth2Client": {...}
            }

        Business Rules:
            - Name uniqueness constraint is enforced within the organisation
            - Configuration must belong to the authenticated user's organisation

        Errors:
            - 400: Validation errors or duplicate client name
            - 404: Configuration not found or not owned by user's organisation
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OrganisationOAuth2ClientsCreateSerializer(
            client, data=request.data
        )
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return JsonResponse(
                    {
                        "error": "duplicate_name",
                        "error_description": "Client name must be unique within the organisation",
                    },
                    status=400,
                )
            response_serializer = OrganisationOAuth2ClientsSerializer(client)
            response_data = {"organisationOAuth2Client": response_serializer.data}
            return JsonResponse(response_data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> Response:
        """
        Delete an external OAuth2 client configuration.

        Business Logic:
            Permanently removes the stored external OAuth2 client configuration.
            This action is irreversible and should be used when the external
            service integration is no longer needed.

        Args:
            pk: The UUID primary key of the external OAuth2 client to delete.

        Response:
            204 No Content on successful deletion.

        Business Rules:
            - Configuration must belong to the authenticated user's organisation
            - Deletion is permanent and cannot be undone
            - Any integrations using this configuration will stop working
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganisationOAuth2ClientsView(APIView):
    """
    API view for listing all external OAuth2 client configurations.

    This endpoint provides a paginated list of all external OAuth2 client
    configurations that have been stored by the authenticated user's organisation.

    Business Context:
        Allows organisation administrators to view all their stored credentials
        for external services in one place, facilitating credential management
        and auditing.

    Authentication:
        Requires JWT authentication. Only the organisation administrator
        can view the list of external client configurations.

    Response Format:
        {
            "organisationOAuth2Client": [...],
            "pagination": {
                "currentPage": int,
                "totalPages": int,
                "totalItems": int,
                "itemsPerPage": int
            }
        }
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OrganisationOAuth2Clients]:
        """
        Filter external OAuth2 client configurations to only return those
        belonging to the authenticated user's organisation.

        Returns:
            QuerySet of OrganisationOAuth2Clients belonging to the user's
            organisation, or an empty QuerySet if user is not an admin.
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OrganisationOAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OrganisationOAuth2Clients.objects.none()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all external OAuth2 client configurations for the organisation.

        Business Logic:
            Returns a paginated list of all external OAuth2 client configurations
            associated with the organisation. Used for viewing and managing
            all stored external service credentials.

        Query Parameters:
            - page: Page number for pagination (default: 1)
            - pageSize: Number of items per page (default: system default)

        Response Format (200 OK):
            {
                "organisationOAuth2Client": [
                    {
                        "id": "uuid",
                        "name": "string",
                        "client_id": "string",
                        ...
                    },
                    ...
                ],
                "pagination": {...}
            }
        """
        clients = self.get_queryset()
        serializer = OrganisationOAuth2ClientsSerializer(clients, many=True)

        oauth_clients, pagination_data = paginate_queryset(
            cast(list[Any], serializer.data), request
        )
        response_data = {
            "organisationOAuth2Client": oauth_clients,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)
