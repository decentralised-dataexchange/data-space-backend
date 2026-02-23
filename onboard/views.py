from __future__ import annotations

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
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
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
    """
    Create a new dataspace user account.

    This endpoint handles user registration for the dataspace platform.
    It creates a new user account with the provided credentials. This is
    a standalone user creation endpoint without organisation association.

    Authentication: None required (public endpoint).

    Request format:
        POST with user registration data as defined in RegisterDataspaceUserSerializer.

    Response format:
        201 Created: Returns the created user data.
        400 Bad Request: Validation errors in the registration data.

    Business rules:
        - Email must be unique across the platform.
        - Password must meet security requirements defined in the serializer.
    """

    model = get_user_model()
    permission_classes = [permissions.AllowAny]  # Or anon users can't register
    serializer_class = RegisterDataspaceUserSerializer


class UserDetail(APIView):
    """
    Retrieve the authenticated user's profile information.

    This endpoint provides access to the current user's account details
    including their name, email, and other profile information.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User can only access their own profile (IsOwnerOrReadOnly).
    """

    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve the current authenticated user's profile.

        Returns the complete user profile data for the authenticated user.
        This endpoint is used to display user account information in the
        frontend dashboard.

        Returns:
            Response: User profile data serialized via DataspaceUserSerializer.
        """
        user = cast(DataspaceUser, request.user)
        serializer = self.serializer_class(user, many=False)
        return Response(serializer.data)


class UserLogin(TokenObtainPairView):  # type: ignore[misc]
    """
    Authenticate users and issue JWT tokens.

    This endpoint handles user login by validating credentials and returning
    JWT access and refresh tokens for authenticated API access.

    Authentication: None required (login endpoint).

    Request format:
        POST with JSON body:
        {
            "email": "user@example.com",
            "password": "userpassword"
        }

    Response format:
        200 OK: Returns JWT tokens (access and refresh).
        401 Unauthorized: Invalid credentials.
        403 Forbidden: Admin users attempting to use this endpoint.

    Business rules:
        - Admin (staff) users are not permitted to login through this endpoint.
        - Admin users must use the Django admin interface for authentication.
        - Regular users receive JWT tokens upon successful authentication.
    """

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Process login request and return JWT tokens.

        Validates user credentials and ensures the user is not an admin.
        Admin users are blocked from using this endpoint as they should
        use the Django admin interface instead.

        Args:
            request: Contains email and password in the request body.

        Returns:
            Response: JWT access and refresh tokens on success.

        Raises:
            403 Forbidden: If the user is a staff/admin user.
            401 Unauthorized: If credentials are invalid (handled by parent).
        """
        if request.data.get("email") and request.data.get("password"):
            user_email = request.data.get("email")
            user = DataspaceUser.objects.filter(email=user_email).first()
            if user and user.is_staff:
                return Response(
                    {"detail": "No active account found with the given credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        return Response(super().post(request, *args, **kwargs).data)


class LogoutView(APIView):
    """
    Logout by blacklisting the provided refresh token.

    This endpoint invalidates a refresh token so it can no longer be used
    to obtain new access tokens. The existing short-lived access token
    will expire naturally within its configured lifetime.

    Authentication: JWT token required.

    Request format:
        POST with JSON body:
        {
            "refresh": "<refresh_token>"
        }

    Response format:
        200 OK: Token successfully blacklisted.
        400 Bad Request: Token is invalid, expired, or missing.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Token is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_200_OK)


class CreateUserAndOrganisationView(APIView):
    """
    Register a new user along with their organisation in a single transaction.

    This is the primary onboarding endpoint for new organisations joining the
    dataspace. It creates both the admin user account and the associated
    organisation profile in an atomic transaction to ensure data consistency.

    Authentication: None required (public registration endpoint).

    Request format:
        POST with JSON body:
        {
            "name": "Admin Name",
            "email": "admin@org.com",
            "password": "securepassword",
            "confirmPassword": "securepassword",
            "organisation": {
                "name": "Organisation Name",
                "sector": "Healthcare",
                "location": "City, Country",
                "policyUrl": "https://org.com/policy",
                "description": "Organisation description",
                "verificationRequestURLPrefix": "https://ows.org.com" (optional)
            },
            "openApiUrl": "https://api.org.com/openapi" (optional)
        }

    Response format:
        201 Created: Returns both user and organisation data.
        400 Bad Request: Validation errors or duplicate admin.

    Business rules:
        - Password and confirmPassword must match.
        - One admin can only have one organisation.
        - Default cover and logo images are assigned automatically.
        - All operations are atomic - either both user and organisation
          are created, or neither is (rollback on failure).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new user and organisation together.

        Handles the complete onboarding flow for new organisations by creating
        the admin user and organisation in a single atomic transaction. This
        ensures that if any part of the registration fails, no partial data
        is left in the database.

        The method performs the following:
        1. Validates all required fields for user and organisation.
        2. Verifies password confirmation matches.
        3. Creates the user account.
        4. Creates the organisation linked to the user.
        5. Assigns default images for cover and logo.

        Args:
            request: Registration data including user and organisation details.

        Returns:
            Response: Created user and organisation data on success.

        Raises:
            400 Bad Request: Missing fields, password mismatch, or duplicate admin.
        """
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
    """
    Retrieve available industry sectors for organisation classification.

    This endpoint provides the list of predefined industry sectors that
    organisations can select during registration or profile updates.
    Sectors are used to categorize organisations within the dataspace.

    Authentication: None required (public endpoint).

    Response format:
        200 OK: Returns a list of available sectors.
        {
            "sectors": [
                {"id": "uuid", "sectorName": "Healthcare"},
                ...
            ]
        }

    Business rules:
        - If no sectors exist in the database, a default 'Healthcare'
          sector is automatically created.
        - Sectors are managed by administrators via Django admin.
    """

    permission_classes: list[Any] = []  # Make it a public route

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve all available sectors.

        Returns the complete list of industry sectors available for
        organisation classification. This data is typically used in
        dropdown menus during organisation registration and editing.

        If the sectors table is empty, initializes it with a default
        'Healthcare' sector to ensure the system always has at least
        one option available.

        Returns:
            Response: List of sectors with their IDs and names.
        """
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
    Download the active Code of Conduct PDF document.

    This endpoint serves the latest active Code of Conduct document that
    all participating organisations must agree to. The Code of Conduct
    outlines the rules, responsibilities, and ethical guidelines for
    dataspace participants.

    Authentication: None required (public endpoint).

    Response format:
        200 OK: Returns the PDF file as a binary download.
        404 Not Found: No active Code of Conduct available.
        500 Internal Server Error: PDF content missing or retrieval error.

    Business rules:
        - Only the most recently updated active Code of Conduct is served.
        - The Code of Conduct is managed by administrators via Django admin.
        - Organisations must accept the Code of Conduct during onboarding.
    """

    permission_classes: list[Any] = []  # Public endpoint

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response | FileResponse:
        """
        Download the latest active Code of Conduct PDF.

        Retrieves the most recently updated Code of Conduct document that
        is marked as active. The document is returned as a PDF file download.

        Returns:
            FileResponse: The Code of Conduct PDF as a downloadable file.
            Response: Error response if no active document exists.

        Raises:
            404 Not Found: If no active Code of Conduct exists in the database.
            500 Internal Server Error: If PDF content is missing or corrupted.
        """
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
