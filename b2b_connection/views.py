from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from b2b_connection.models import B2BConnection
from b2b_connection.serializers import B2BConnectionSerializer, B2BConnectionsSerializer
from dataspace_backend.utils import paginate_queryset
from organisation.models import Organisation


# Create your views here.
class B2BConnectionView(APIView):
    """
    View for B2BConnection CRUD operations.
    Organisations can manage their own B2B connections.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return B2BConnection.objects.filter(organisationId=organisation)
        except Organisation.DoesNotExist:
            return B2BConnection.objects.none()

    def get(self, request, pk):
        """Get specific client"""
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = B2BConnectionSerializer(client)
        response_data = {"b2bConnection": serializer.data}
        return JsonResponse(response_data)


class B2BConnectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return B2BConnection.objects.filter(organisationId=organisation)
        except Organisation.DoesNotExist:
            return B2BConnection.objects.none()

    def get(self, request):
        """List all connections"""
        # List all clients
        clients = self.get_queryset()
        serializer = B2BConnectionsSerializer(clients, many=True)

        b2b_connections, pagination_data = paginate_queryset(serializer.data, request)
        response_data = {
            "b2bConnection": b2b_connections,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)
