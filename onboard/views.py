from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from onboard.permissions import IsOwnerOrReadOnly
from .serializers import (DataspaceUserSerializer,
                          RegisterDataspaceUserSerializer)
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)
from django.contrib.auth import get_user_model

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
    

class UserLogin(TokenObtainPairView):

    def post(self, request, *args, **kwargs):
        if request.data.get('email') and request.data.get('password'):
            User = get_user_model()
            user_email = request.data.get('email')
            user = User.objects.filter(email=user_email).first()
            if user and user.is_staff:
                return Response({"Error": "Admin users are not allowed to login"}, status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)
    
