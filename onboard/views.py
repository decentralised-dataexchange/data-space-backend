import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from onboard.permissions import IsOwnerOrReadOnly
from .serializers import (DataspaceUserSerializer,
                          RegisterDataspaceUserSerializer)
from organisation.models import Organisation, Sector, CodeOfConduct
from organisation.serializers import OrganisationSerializer, SectorSerializer
from dataspace_backend.image_utils import (
    construct_cover_image_url,
    construct_logo_image_url,
    load_default_image,
)

logger = logging.getLogger(__name__)


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

        # Extract organisation details from the new structure
        organisation_data = data.get("organisation", {})
        
        # Define required fields for both user and organisation
        required_fields = [
            "name",
            "email",
            "password",
            "confirmPassword",
            "organisation",
        ]
        organisation_required_fields = [
            "name",
            "sector",
            "location",
            "policyUrl",
            "description",
        ]

        # Combine required fields
        all_required_fields = required_fields + organisation_required_fields

        # Check for missing fields in both user and organisation data
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Check for missing fields in both user and organisation data
        missing_fields = [f for f in organisation_required_fields if not organisation_data.get(f)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if passwords match
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
                    name=data.get("name")
                )

                if Organisation.objects.filter(admin=user).exists():
                    return Response(
                        {"error": "An Organisation already exists for this admin"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                organisation = Organisation.objects.create(
                    name=organisation_data.get("name"),
                    sector=organisation_data.get("sector"),
                    location=organisation_data.get("location"),
                    policyUrl=organisation_data.get("policyUrl"),
                    description=organisation_data.get("description"),
                    owsBaseUrl=organisation_data.get("verificationRequestURLPrefix", ""),
                    openApiUrl=data.get("openApiUrl", ""),
                    admin=user,
                )

                # Add default cover image and logo image URL
                cover_image_id = load_default_image("cover.jpeg")
                logo_image_id = load_default_image("unknownOrgLogo.png")
                organisation.coverImageId = cover_image_id
                organisation.logoId = logo_image_id

                # Update organisation with cover and logo image URL
                organisation.coverImageUrl = construct_cover_image_url(
                    baseurl=request.get_host(),
                    entity_id=str(organisation.id),
                    entity_type="organisation",
                    is_public_endpoint=True
                )
                organisation.logoUrl = construct_logo_image_url(
                    baseurl=request.get_host(),
                    entity_id=str(organisation.id),
                    entity_type="organisation",
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
    
class SectorView(APIView):
    
    permission_classes = []  # Make it a public route
    
    def get(self, request):
        # Check if any sectors exist
        sectors = Sector.objects.all()
        
        # If no sectors exist, create the default 'Healthcare' sector
        if not sectors.exists():
            Sector.objects.create(sectorName="Healthcare")
            sectors = Sector.objects.all()
        
        serializer = SectorSerializer(sectors, many=True)
        return Response({"sectors": serializer.data}, status=status.HTTP_200_OK)
    
class CodeOfConductView(APIView):
    """
    API endpoint to get the latest active code of conduct PDF.
    This is a public endpoint.
    """
    permission_classes = []  # Public endpoint

    def get(self, request):
        try:
            logger.info("Attempting to fetch latest active code of conduct")
            
            # Get the latest active code of conduct
            code_of_conduct = CodeOfConduct.objects.filter(isActive=True).latest('updatedAt')
            
            if not code_of_conduct.pdfFile:
                logger.error("Code of conduct found but PDF file is missing")
                return Response(
                    {"error": "Code of conduct PDF file is missing"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            logger.info(f"Serving code of conduct: {code_of_conduct.pdfFile.name}")
            
            # Return the file directly for download
            response = FileResponse(
                code_of_conduct.pdfFile,
                as_attachment=True,
                filename=f"code_of_conduct_{code_of_conduct.updatedAt.date()}.pdf"
            )
            return response
            
        except CodeOfConduct.DoesNotExist:
            logger.warning("No active code of conduct found in the database")
            return Response(
                {"error": "No active code of conduct available"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error serving code of conduct")
            return Response(
                {"error": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
