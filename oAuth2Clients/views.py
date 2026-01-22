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
    View for OAuth2Client CRUD operations.
    Organisations can manage their own OAuth clients.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OAuth2Clients]:
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OAuth2Clients.objects.none()

    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> JsonResponse:
        """Get specific client"""
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OAuth2ClientsSerializer(client)
        response_data = {"oAuth2Client": serializer.data}
        return JsonResponse(response_data)

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """Create new OAuth client"""
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
        """Update OAuth client"""
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
        """Hard delete OAuth client"""
        client = get_object_or_404(self.get_queryset(), pk=pk)
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OAuth2ClientsView(APIView):
    """
    View for OAuth2Clients CRUD operations.
    Organisations can manage their own OAuth clients.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OAuth2Clients]:
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OAuth2Clients.objects.none()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """List all clients"""
        # List all clients
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
    View for OrganisationOAuth2ClientView CRUD operations.
    Organisations can manage their external OAuth clients.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OrganisationOAuth2Clients]:
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OrganisationOAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OrganisationOAuth2Clients.objects.none()

    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> JsonResponse:
        """Get specific client"""
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = OrganisationOAuth2ClientsSerializer(client)
        response_data = {"organisationOAuth2Client": serializer.data}
        return JsonResponse(response_data)

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """Create new OAuth client"""
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
        """Update OAuth client"""
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
        """Hard delete OAuth client"""
        client = get_object_or_404(self.get_queryset(), pk=pk)
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganisationOAuth2ClientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[OrganisationOAuth2Clients]:
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return OrganisationOAuth2Clients.objects.filter(organisation=organisation)
        except Organisation.DoesNotExist:
            return OrganisationOAuth2Clients.objects.none()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """List all clients"""
        # List all clients
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
