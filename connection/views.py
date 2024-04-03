from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.http import JsonResponse
from .serializers import DISPConnectionSerializer
from config.models import DataSource
from .models import Connection
from uuid import uuid4
from dataspace_backend.utils import paginate_queryset
from dataspace_backend.settings import DATA_MARKETPLACE_DW_URL, DATA_MARKETPLACE_APIKEY
import requests

# Create your views here.


class DISPConnectionView(APIView):
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Call digital wallet to create connection
        url = f"{DATA_MARKETPLACE_DW_URL}/v2/connections/create-invitation?multi_use=false&auto_accept=true"
        authorization_header = DATA_MARKETPLACE_APIKEY

        try:
            response = requests.post(
                url, headers={"Authorization": authorization_header}
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
                url, headers={"Authorization": authorization_header}
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

        try:
            connection = Connection.objects.get(dataSourceId=datasource)
            connection.connectionId = connection_id
            connection.connectionState = "invitation"
            connection.connectionRecord = {}
            connection.save()
        except Connection.DoesNotExist:
            connection = Connection.objects.create(
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
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            connections = Connection.objects.filter(dataSourceId=datasource)
            connections, pagination_data = paginate_queryset(connections, request)
            serializer = DISPConnectionSerializer(connections, many=True)
            connection_data = serializer.data

        except Connection.DoesNotExist:
            # If no connection exists, return empty data
            connection_data = None
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
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, connectionId):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

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
