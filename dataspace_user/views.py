from rest_framework import generics
from .models import DataspaceUser
from .serializers import DataspaceUserSerializer, RegisterDataspaceUserSerializer
from rest_framework import permissions
from .permissions import IsOwnerOrReadOnly
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import CreateAPIView
from django.contrib.auth import get_user_model


# Create your views here.

class CreateUserView(CreateAPIView):

    model = get_user_model()
    permission_classes = [
        permissions.AllowAny # Or anon users can't register
    ]
    serializer_class = RegisterDataspaceUserSerializer

class UserList(generics.ListAPIView):
    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        email = self.request.user.email
        return DataspaceUser.objects.filter(email=email)


class UserDetail(generics.RetrieveAPIView):
    queryset = DataspaceUser.objects.all()
    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


