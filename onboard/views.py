from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .permissions import IsOwnerOrReadOnly
from .serializers import (DataspaceUserSerializer,
                          RegisterDataspaceUserSerializer)

# Create your views here.


class CreateUserView(CreateAPIView):

    model = get_user_model()
    permission_classes = [permissions.AllowAny]  # Or anon users can't register
    serializer_class = RegisterDataspaceUserSerializer


class UserDetail(APIView):
    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request):
        serializer = self.serializer_class(request.user, many=False)
        return Response(serializer.data)
