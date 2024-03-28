from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.http import JsonResponse
from .serializers import DISPConnectionSerializer
from config.models import DataSource
from .models import Connection
from uuid import uuid4

# Create your views here.


class DISPConnectionView(APIView):
    serializer_class = DISPConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        body = request.data
        connection_url = body.get("connectionUrl", None)
        if connection_url is not None:
            # Call digital wallet to create connection
            # Add dummy connection
            connection_id = str(uuid4())
            response = {
                "connection": {
                    "id": "6604ffdf8b3a694e41bf8819",
                    "connectionId": connection_id,
                    "state": "request",
                    "myDid": "i716Uo4FUXk4KuebxXBKT",
                    "theirLabel": "Jacobsons lumber yard",
                    "routingState": "none",
                    "invitationKey": "REDACTED_INVITATION_KEY",
                    "invitationMode": "once",
                    "initiator": "external",
                    "updatedAt": "2024-03-28 05:27:59.175831Z",
                    "accept": "auto",
                    "requestId": "fa37dc61-7761-4851-a650-60e935356a0c",
                    "createdAt": "2024-03-28 05:27:59.142181Z",
                    "alias": "",
                    "errorMsg": "",
                    "inboundConnectionId": "",
                    "theirDid": "",
                    "theirRole": ""
                }
            }
            connection_data = response["connection"]
            connection_data.pop("id", None)

            serializer = self.serializer_class(data=connection_data)
            if serializer.is_valid():

                try:
                    connection = Connection.objects.get(
                        dataSourceId=datasource)
                    # Update the existing connection with new data
                    for key, value in connection_data.items():
                        setattr(connection, key, value)

                    connection.save()

                except Connection.DoesNotExist:
                    connection = Connection.objects.create(
                        dataSourceId=datasource, **serializer.validated_data)

                # Serialize the created instance to match the response format
                response_serializer = self.serializer_class(connection)
                return JsonResponse({'connection': response_serializer.data}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return JsonResponse({'error': "Connection response validation failed"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({'error': "Connection url required"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = Connection.objects.get(dataSourceId=datasource)
            connection_serializer = self.serializer_class(
                connection)
            connection_data = connection_serializer.data
        except Connection.DoesNotExist:
            # If no connection exists, return empty data
            connection_data = None

        # Construct the response data
        response_data = {
            'connection': connection_data,
        }

        return JsonResponse(response_data)

    def delete(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            connection = Connection.objects.get(dataSourceId=datasource)
            connection.delete()
            return JsonResponse({'message': 'Connection deleted successfully'}, status=status.HTTP_200_OK)
        except Connection.DoesNotExist:
            # If no connection exists, return error
            return JsonResponse({'error': 'Data source connection not found'}, status=status.HTTP_400_BAD_REQUEST)


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
            serializer = DISPConnectionSerializer(connections, many=True)
            connection_data = serializer.data

        except Connection.DoesNotExist:
            # If no connection exists, return empty data
            connection_data = None

        # Construct the response data
        response_data = {
            'connections': connection_data,
        }

        return JsonResponse(response_data)
