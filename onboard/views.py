import io
import logging
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from dataspace_backend.image_utils import (
    construct_cover_image_url,
    construct_logo_image_url,
    load_default_image,
)
from onboard.models import DataspaceUser
from onboard.permissions import IsOwnerOrReadOnly
from organisation.models import CodeOfConduct, Organisation, Sector
from organisation.serializers import OrganisationSerializer, SectorSerializer

from .serializers import DataspaceUserSerializer, RegisterDataspaceUserSerializer

logger = logging.getLogger(__name__)


class CreateUserView(CreateAPIView):  # type: ignore[type-arg]
    model = get_user_model()
    permission_classes = [permissions.AllowAny]  # Or anon users can't register
    serializer_class = RegisterDataspaceUserSerializer


class UserDetail(APIView):
    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(DataspaceUser, request.user)
        serializer = self.serializer_class(user, many=False)
        return Response(serializer.data)


class UserLogin(TokenObtainPairView):  # type: ignore[misc]
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        if request.data.get("email") and request.data.get("password"):
            user_email = request.data.get("email")
            user = DataspaceUser.objects.filter(email=user_email).first()
            if user and user.is_staff:
                return Response(
                    {"Error": "Admin users are not allowed to login"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return Response(super().post(request, *args, **kwargs).data)


class CreateUserAndOrganisationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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

        # Check for missing fields in both user and organisation data
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for missing fields in both user and organisation data
        missing_fields = [
            f for f in organisation_required_fields if not organisation_data.get(f)
        ]
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

        try:
            with transaction.atomic():
                user = DataspaceUser.objects.create_user(
                    email=str(data.get("email", "")),
                    password=str(data.get("password", "")),
                    name=str(data.get("name", "")),
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
                    owsBaseUrl=organisation_data.get(
                        "verificationRequestURLPrefix", ""
                    ),
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
                    is_public_endpoint=True,
                )
                organisation.logoUrl = construct_logo_image_url(
                    baseurl=request.get_host(),
                    entity_id=str(organisation.id),
                    entity_type="organisation",
                    is_public_endpoint=True,
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
    permission_classes: list[Any] = []  # Make it a public route

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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

    permission_classes: list[Any] = []  # Public endpoint

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response | FileResponse:
        try:
            logger.info("Attempting to fetch latest active code of conduct")

            # Get the latest active code of conduct
            code_of_conduct = CodeOfConduct.objects.filter(isActive=True).latest(
                "updatedAt"
            )

            if not code_of_conduct.pdfContent:
                logger.error("Code of conduct found but PDF content is missing")
                return Response(
                    {"error": "Code of conduct PDF content is missing"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            logger.info(f"Serving code of conduct: {code_of_conduct.pdfFileName}")

            # Create a BytesIO object from the binary content
            pdf_buffer = io.BytesIO(code_of_conduct.pdfContent)

            # Determine filename
            filename = (
                code_of_conduct.pdfFileName
                or f"code_of_conduct_{code_of_conduct.updatedAt.date()}.pdf"
            )

            # Return the file directly for download
            response = FileResponse(
                pdf_buffer,
                as_attachment=True,
                filename=filename,
                content_type="application/pdf",
            )
            return response

        except CodeOfConduct.DoesNotExist:
            logger.warning("No active code of conduct found in the database")
            return Response(
                {"error": "No active code of conduct available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            logger.exception("Error serving code of conduct")
            return Response(
                {"error": "An error occurred while processing your request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
