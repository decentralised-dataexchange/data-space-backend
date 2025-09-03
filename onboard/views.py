import os
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from onboard.permissions import IsOwnerOrReadOnly
from .serializers import (DataspaceUserSerializer,
                          RegisterDataspaceUserSerializer)
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)
from django.http import HttpResponse, JsonResponse
from dataspace_backend import settings
from organisation.models import Organisation
from organisation.serializers import OrganisationSerializer
from config.models import ImageModel

# Create your views here.
def construct_cover_image_url(
    baseurl: str,
    organisation_id: str,
    is_public_endpoint: bool = False
):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/organisation/{organisation_id}/coverimage/"
    return f"{protocol}{baseurl}{endpoint}"


def construct_logo_image_url(
    baseurl: str,
    organisation_id: str,
    is_public_endpoint: bool = False
):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/organisation/{organisation_id}/logoimage/"
    return f"{protocol}{baseurl}{endpoint}"

def load_default_cover_image():
    cover_image_path = os.path.join(settings.BASE_DIR, "resources","assets", "cover.jpeg")

    with open(cover_image_path, 'rb') as cover_image_file:
        image_data = cover_image_file.read()
        image = ImageModel(image_data=image_data)
        image.save()
        return image.id

def load_default_logo_image():
    logo_image_path = os.path.join(settings.BASE_DIR, "resources","assets", "logo.jpeg")

    with open(logo_image_path, 'rb') as logo_image_file:
        image_data = logo_image_file.read()
        image = ImageModel(image_data=image_data)
        image.save()
        return image.id



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
    
class CreateUserAndOrganisationView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}

        required_fields = [
            "email",
            "password",
            "confirmPassword",
            "name",
            "sector",
            "location",
            "policyUrl",
            "description",
            "owsBaseUrl",
        ]

        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data.get("password") != data.get("confirmPassword"):
            return Response(
                {"error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=data.get("email"),
                    password=data.get("password"),
                )

                if Organisation.objects.filter(admin=user).exists():
                    return Response(
                        {"error": "An Organisation already exists for this admin"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                organisation = Organisation.objects.create(
                    name=data.get("name"),
                    sector=data.get("sector"),
                    location=data.get("location"),
                    policyUrl=data.get("policyUrl"),
                    description=data.get("description"),
                    owsBaseUrl=data.get("owsBaseUrl", ""),
                    openApiUrl=data.get("openApiUrl", ""),
                    admin=user,
                )

                # Add default cover image and logo image URL
                cover_image_id = load_default_cover_image()
                logo_image_id = load_default_logo_image()
                organisation.coverImageId = cover_image_id
                organisation.logoId = logo_image_id

                # Update organisation with cover and logo image URL
                organisation.coverImageUrl = construct_cover_image_url(
                    baseurl=request.get_host(),
                    organisation_id=str(organisation.id),
                    is_public_endpoint=True
                )
                organisation.logoUrl = construct_logo_image_url(
                    baseurl=request.get_host(),
                    organisation_id=str(organisation.id),
                    is_public_endpoint=True
                )
                organisation.save()

        except Exception as e:
            return Response(
                {"error": f"Failed to register: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_payload = DataspaceUserSerializer(user).data
        org_payload = OrganisationSerializer(organisation).data

        return Response(
            {"user": user_payload, "organisation": org_payload},
            status=status.HTTP_201_CREATED,
        )
    
