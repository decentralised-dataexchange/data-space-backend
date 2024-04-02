from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.http import JsonResponse
from .serializers import DISPConnectionSerializer
from config.models import DataSource
from .models import Connection
from uuid import uuid4
from dataspace_backend.utils import paginate_queryset

# Create your views here.


class DISPConnectionView(APIView):
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Call digital wallet to create connection
        # Add dummy connection
        connection_id = str(uuid4())
        response = {
            "connection": {
                "connectionId": connection_id,
                "invitation": {
                    "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation",
                    "@id": "7b4e6658-1489-4b2d-9716-f5ac872da95d",
                    "serviceEndpoint": "https://cloudagent.igrant.io/v1/64ec561de2f6a8000142c671/agent/",
                    "label": "Jacobsons lumber yard",
                    "imageUrl": "https://staging-api.igrant.io/v2/onboard/image/64ee65d1e2f6a8000142c687/web",
                    "recipientKeys": [
                        "6wobAAgEaSWgGYGB4uTpTfkDwnyXcZRX61JZNRZEx5ME"
                    ]
                },
                "invitationUrl": "https://cloudagent.igrant.io/v1/64ec561de2f6a8000142c671/agent/?c_i=eyJAdHlwZSI6ICJkaWQ6c292OkJ6Q2JzTlloTXJqSGlxWkRUVUFTSGc7c3BlYy9jb25uZWN0aW9ucy8xLjAvaW52aXRhdGlvbiIsICJAaWQiOiAiN2I0ZTY2NTgtMTQ4OS00YjJkLTk3MTYtZjVhYzg3MmRhOTVkIiwgImxhYmVsIjogIkphY29ic29ucyBsdW1iZXIgeWFyZCIsICJzZXJ2aWNlRW5kcG9pbnQiOiAiaHR0cHM6Ly9jbG91ZGFnZW50LmlncmFudC5pby92MS82NGVjNTYxZGUyZjZhODAwMDE0MmM2NzEvYWdlbnQvIiwgImltYWdlVXJsIjogImh0dHBzOi8vc3RhZ2luZy1hcGkuaWdyYW50LmlvL3YyL29uYm9hcmQvaW1hZ2UvNjRlZTY1ZDFlMmY2YTgwMDAxNDJjNjg3L3dlYiIsICJyZWNpcGllbnRLZXlzIjogWyJBbkxoUDRURVJ0eWFieWp5RHV1cXJtNGdiSGVrUENrS1NIRGdrMlhubmZXeiJdfQ=="
            },
            "firebaseDynamicLink": "https://datawallet.page.link/cncod1Qu52vzR3bU7"
        }
        connection_record = response['connection']

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
                connectionRecord={}
            )

        return JsonResponse(response)


class DISPConnectionsView(APIView):
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            connections = Connection.objects.filter(dataSourceId=datasource)
            connections, pagination_data = paginate_queryset(
                connections, request)
            serializer = DISPConnectionSerializer(connections, many=True)
            connection_data = serializer.data

        except Connection.DoesNotExist:
            # If no connection exists, return empty data
            connection_data = None
            pagination_data = {
                'currentPage': 0,
                'totalItems': 0,
                'totalPages': 0,
                'limit': 0,
                'hasPrevious': False,
                'hasNext': False
            }

        # Construct the response data
        response_data = {
            'connections': connection_data,
            'pagination': pagination_data
        }

        return JsonResponse(response_data)


class DISPDeleteConnectionView(APIView):
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, connectionId):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = Connection.objects.get(
                pk=connectionId, dataSourceId=datasource)
            connection.delete()
            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        except Connection.DoesNotExist:
            # If no connection exists, return error
            return JsonResponse({'error': 'Data source connection not found'}, status=status.HTTP_400_BAD_REQUEST)
