from __future__ import annotations

from typing import Any, cast

import requests
from django.http import HttpRequest, HttpResponse, JsonResponse
from dj_rest_auth.serializers import PasswordChangeSerializer
from dj_rest_auth.views import sensitive_post_parameters_m
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from connection.models import Connection
from dataspace_backend.image_utils import (
    construct_cover_image_url,
    construct_logo_image_url,
    get_image_response,
    load_default_image,
    update_entity_image,
)
from dataspace_backend.settings import DATA_MARKETPLACE_APIKEY, DATA_MARKETPLACE_DW_URL
from dataspace_backend.utils import get_datasource_or_400
from onboard.models import DataspaceUser
from onboard.serializers import DataspaceUserSerializer

from .models import DataSource, Verification, VerificationTemplate
from .serializers import (
    DataSourceSerializer,
    VerificationSerializer,
    VerificationTemplateSerializer,
)


class DataSourceView(APIView):
    """
    Manage data source configuration and profile.

    A data source represents an entity that provides data within the dataspace
    ecosystem. This endpoint allows authenticated admins to create, retrieve,
    and update their data source configuration including metadata, URLs,
    and verification status.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - Each admin can only have one data source.
    """

    serializer_class = DataSourceSerializer
    verification_serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Create a new data source for the authenticated admin.

        Creates a data source profile with the provided configuration.
        Default cover and logo images are automatically assigned.
        Each admin can only create one data source.

        Request format:
            POST with JSON body:
            {
                "dataSource": {
                    "name": "Data Source Name",
                    "description": "Description",
                    "location": "City, Country",
                    "policyUrl": "https://datasource.com/policy"
                }
            }

        Response format:
            201 Created: Returns the created data source configuration.
            400 Bad Request: Validation errors or admin already has a data source.

        Business rules:
            - One admin can only have one data source.
            - Default images are assigned automatically.
            - Image URLs are constructed based on the entity ID.

        Returns:
            JsonResponse: Created data source data.
        """
        admin = request.user

        # Check if a DataSource with the same admin already exists
        if DataSource.objects.filter(admin=admin).exists():
            return JsonResponse(
                {"error": "A DataSource already exists for this admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data = request.data.get("dataSource", {})

        request_data["coverImageUrl"] = "nil"
        request_data["logoUrl"] = "nil"

        request_data["openApiUrl"] = ""

        # Create and validate the DataSource serializer
        serializer = self.serializer_class(data=request_data)
        if serializer.is_valid():
            datasource = DataSource.objects.create(
                admin=admin, **serializer.validated_data
            )

            # Add default cover image and logo image URL
            cover_image_id = load_default_image("cover.jpeg")
            logo_image_id = load_default_image("logo.jpeg")
            datasource.coverImageId = cover_image_id
            datasource.logoId = logo_image_id

            # Update data source with cover and logo image URL
            datasource.coverImageUrl = construct_cover_image_url(
                baseurl=request.get_host(),
                entity_id=str(datasource.id),
                entity_type="data-source",
                is_public_endpoint=True,
            )
            datasource.logoUrl = construct_logo_image_url(
                baseurl=request.get_host(),
                entity_id=str(datasource.id),
                entity_type="data-source",
                is_public_endpoint=True,
            )
            datasource.save()

            # Serialize the created instance to match the response format
            response_serializer = self.serializer_class(datasource)
            return JsonResponse(
                {"dataSource": response_serializer.data}, status=status.HTTP_201_CREATED
            )

        return JsonResponse(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Retrieve the current user's data source profile and verification status.

        Returns the complete data source configuration along with any
        associated verification information. This provides a comprehensive
        view of the data source's current state in the dataspace.

        Response format:
            {
                "dataSource": {
                    "id": "uuid",
                    "name": "Data Source Name",
                    "description": "...",
                    "location": "...",
                    "policyUrl": "...",
                    "coverImageUrl": "...",
                    "logoUrl": "...",
                    ...
                },
                "verification": {
                    "id": "uuid",
                    "dataSourceId": "uuid",
                    "presentationExchangeId": "string",
                    "presentationState": "verified|pending|...",
                    "presentationRecord": {...}
                }
            }

        Returns:
            JsonResponse: Data source profile and verification status.
            Response: Error if user has no associated data source.
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        # Serialize the DataSource instance
        datasource_serializer = self.serializer_class(datasource)

        verification_result: dict[str, Any]
        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification_serializer = self.verification_serializer_class(verification)
            verification_result = verification_serializer.data
        except Verification.DoesNotExist:
            # If no Verification exists, return empty data
            verification_result = {
                "id": "",
                "dataSourceId": "",
                "presentationExchangeId": "",
                "presentationState": "",
                "presentationRecord": {},
            }

        # Construct the response data
        response_data = {
            "dataSource": datasource_serializer.data,
            "verification": verification_result,
        }

        return JsonResponse(response_data)

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Update the current user's data source profile.

        Allows data source admins to update their data source's profile
        information. Only provided fields are updated; missing fields
        retain their current values.

        Request format:
            PUT with JSON body:
            {
                "dataSource": {
                    "name": "Updated Name" (optional),
                    "description": "Updated description" (optional),
                    "location": "New Location" (optional),
                    "policyUrl": "https://new-policy-url.com" (optional)
                }
            }

        Response format:
            200 OK: Returns updated data source data.
            400 Bad Request: User has no associated data source.

        Business rules:
            - Only non-empty fields in the request are updated.
            - Other fields remain unchanged.

        Returns:
            JsonResponse: Updated data source profile.
            Response: Error if user has no associated data source.
        """
        data = request.data.get("dataSource", {})

        # Get the DataSource instance associated with the current user
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update the fields if they are not empty
        if data.get("description"):
            datasource.description = data["description"]
        if data.get("location"):
            datasource.location = data["location"]
        if data.get("name"):
            datasource.name = data["name"]
        if data.get("policyUrl"):
            datasource.policyUrl = data["policyUrl"]

        # Save the updated DataSource instance
        datasource.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(datasource)
        return JsonResponse({"dataSource": serializer.data}, status=status.HTTP_200_OK)


class DataSourceCoverImageView(APIView):
    """
    Manage the data source's cover/banner image.

    This endpoint handles retrieval and upload of the data source's cover
    image, which is typically displayed as a banner on the data source's
    profile page in the dataspace portal.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing data source.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> HttpResponse | Response:
        """
        Retrieve the data source's cover image.

        Returns the data source's cover/banner image as binary data.
        A default image is assigned during data source creation if
        none is uploaded.

        Response format:
            200 OK: Binary image data with appropriate content-type header.
            400 Bad Request: User has no associated data source.
            404 Not Found: Cover image not found in storage.

        Returns:
            HttpResponse: Binary image data.
            Response: Error if data source or image not found.
        """
        # Get the DataSource instance
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return get_image_response(datasource.coverImageId, "Cover image not found")

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Upload a new cover image for the data source.

        Replaces the data source's current cover image with the uploaded
        file. The image is stored and a URL is generated for retrieval.

        Request format:
            PUT with multipart/form-data:
            - orgimage: The image file to upload.

        Response format:
            200 OK: Returns updated data source data with new image URL.
            400 Bad Request: Missing image file or validation error.

        Business rules:
            - The previous cover image is replaced.
            - Image URLs are automatically updated.

        Returns:
            JsonResponse: Updated data source data with new cover image URL.
            Response: Error if validation fails.
        """
        uploaded_image = request.FILES.get("orgimage")

        # Get the DataSource instance
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        return update_entity_image(
            request=request,
            entity=datasource,
            uploaded_image=uploaded_image,
            image_id_attr="coverImageId",
            url_attr="coverImageUrl",
            entity_type="data-source",
        )


class DataSourceLogoImageView(APIView):
    """
    Manage the data source's logo image.

    This endpoint handles retrieval and upload of the data source's logo,
    which is used to represent the data source across the dataspace
    platform (e.g., in listings, headers, and cards).

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing data source.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> HttpResponse | Response:
        """
        Retrieve the data source's logo image.

        Returns the data source's logo as binary data. A default logo
        is assigned during data source creation if none is uploaded.

        Response format:
            200 OK: Binary image data with appropriate content-type header.
            400 Bad Request: User has no associated data source.
            404 Not Found: Logo image not found in storage.

        Returns:
            HttpResponse: Binary image data.
            Response: Error if data source or image not found.
        """
        # Get the DataSource instance
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return get_image_response(datasource.logoId, "Logo image not found")

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Upload a new logo image for the data source.

        Replaces the data source's current logo with the uploaded file.
        The logo is stored and a URL is generated for retrieval.

        Request format:
            PUT with multipart/form-data:
            - orgimage: The logo image file to upload.

        Response format:
            200 OK: Returns updated data source data with new logo URL.
            400 Bad Request: Missing image file or validation error.

        Business rules:
            - The previous logo is replaced.
            - Logo URLs are automatically updated.
            - Logo appears in data source listings and profiles.

        Returns:
            JsonResponse: Updated data source data with new logo URL.
            Response: Error if validation fails.
        """
        uploaded_image = request.FILES.get("orgimage")

        # Get the DataSource instance
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        return update_entity_image(
            request=request,
            entity=datasource,
            uploaded_image=uploaded_image,
            image_id_attr="logoId",
            url_attr="logoUrl",
            entity_type="data-source",
        )


class AdminView(APIView):
    """
    Manage the authenticated admin user's profile.

    This endpoint allows data source administrators to view and update
    their own user profile information within the dataspace system.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
    """

    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Retrieve the authenticated admin's user profile.

        Returns the complete user profile data for the currently
        authenticated administrator.

        Response format:
            {
                "id": "uuid",
                "email": "admin@example.com",
                "name": "Admin Name",
                ...
            }

        Returns:
            JsonResponse: Admin user profile data.
        """
        user = cast(DataspaceUser, request.user)
        serializer = self.serializer_class(user, many=False)
        return JsonResponse(serializer.data)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Update the authenticated admin's user profile.

        Allows administrators to update their profile information.
        Currently supports updating the name field.

        Request format:
            PUT with JSON body:
            {
                "name": "Updated Admin Name"
            }

        Response format:
            200 OK: Returns updated admin profile data.
            400 Bad Request: Missing name field or validation errors.

        Business rules:
            - The name field is required for updates.
            - Email cannot be changed through this endpoint.

        Returns:
            JsonResponse: Updated admin user profile data.
        """
        admin = cast(DataspaceUser, request.user)
        request_data = request.data
        if "name" not in request_data:
            return JsonResponse(
                {"error": "Name field is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.serializer_class(admin, data=request_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DataSourceVerificationView(APIView):
    """
    Manage data source verification through verifiable credentials.

    This endpoint handles the data source's verification process using
    verifiable presentations. Data sources can check their verification
    status or initiate a new verification request through the DISP
    (Data Intermediary Service Provider) connection.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing data source.

    Business context:
        Data source verification establishes trust by requiring data sources
        to present verifiable credentials that prove their identity and
        authorization to participate in the dataspace.
    """

    serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Retrieve the data source's verification status.

        Returns the current state of the data source's verification,
        including the presentation exchange details and verification state.

        Response format:
            {
                "verification": {
                    "id": "uuid",
                    "dataSourceId": "uuid",
                    "presentationExchangeId": "string",
                    "presentationState": "verified|pending|...",
                    "presentationRecord": {...}
                }
            }

        Returns:
            JsonResponse: Verification status and details.
            JsonResponse: Error if no verification record exists.
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification_serializer = self.serializer_class(verification)
        except Verification.DoesNotExist:
            return JsonResponse(
                {"error": "Data source verification not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Construct the response data
        response_data = {
            "verification": verification_serializer.data,
        }

        return JsonResponse(response_data)

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Initiate data source verification.

        Starts the verification process by sending a presentation request
        through the established DISP connection. The data source must have
        an active connection before verification can be initiated.

        This method communicates with the Data Marketplace's digital wallet
        service to create a presentation offer based on the configured
        verification template (data agreement).

        Response format:
            {
                "verification": {
                    "id": "uuid",
                    "dataSourceId": "uuid",
                    "presentationExchangeId": "string",
                    "presentationState": "offer_sent|...",
                    "presentationRecord": {...}
                }
            }

        Business rules:
            - Data source must have an active DISP connection.
            - A VerificationTemplate must be configured in the system.
            - Creates or updates the Verification record.
            - Communicates with external Data Marketplace digital wallet.

        Returns:
            JsonResponse: Initiated verification details with exchange ID.
            JsonResponse: Error if connection/template not found or service fails.
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        try:
            connection = Connection.objects.get(
                dataSourceId=datasource, connectionState="active"
            )
        except Connection.DoesNotExist:
            return JsonResponse(
                {"error": "DISP Connection not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verificationTemplate = VerificationTemplate.objects.first()
        if verificationTemplate is None:
            return JsonResponse(
                {"error": "Verification template not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_agreement_id = verificationTemplate.dataAgreementId
        connection_id = connection.connectionId
        payload = {
            "connection_id": connection_id,
            "template_id": data_agreement_id,
        }
        url = (
            f"{DATA_MARKETPLACE_DW_URL}/present-proof/data-agreement-negotiation/offer"
        )
        authorization_header = DATA_MARKETPLACE_APIKEY
        try:
            response = requests.post(
                url, headers={"Authorization": authorization_header}, json=payload
            )
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.RequestException as e:
            return JsonResponse(
                {"error": f"Error calling digital wallet: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentation_exchange_id = response["presentation_exchange_id"]
        presentation_state = response["state"]
        presentation_record = response

        # Update or create Verification object
        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification.presentationExchangeId = presentation_exchange_id
            verification.presentationState = presentation_state
            verification.presentationRecord = presentation_record
            verification.save()
        except Verification.DoesNotExist:
            verification = Verification.objects.create(
                dataSourceId=datasource,
                presentationExchangeId=presentation_exchange_id,
                presentationState=presentation_state,
                presentationRecord=presentation_record,
            )

        # Serialize the verification object
        verification_serializer = VerificationSerializer(verification)

        # Construct the response data
        response_data = {
            "verification": verification_serializer.data,
        }

        return JsonResponse(response_data)


class VerificationTemplateView(APIView):
    """
    Retrieve available verification templates for data sources.

    Verification templates define the credential schemas and data agreements
    that data sources must satisfy during the verification process. These
    templates are configured by administrators and define what credentials
    are required to verify a data source's identity.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing data source.
    """

    serializer_class = VerificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Retrieve all available verification templates.

        Returns the list of verification templates that can be used for
        data source verification. Each template includes the data source's
        wallet name and location for context.

        Response format:
            {
                "verificationTemplates": [
                    {
                        "id": "uuid",
                        "name": "Template Name",
                        "dataAgreementId": "uuid",
                        "walletName": "Data Source Name",
                        "walletLocation": "Location",
                        ...
                    },
                    ...
                ]
            }

        Business rules:
            - Templates are managed by administrators.
            - Each template response is enriched with the requesting
              data source's wallet name and location.

        Returns:
            JsonResponse: List of verification templates.
            JsonResponse: Error if data source or templates not found.
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vt_objects = VerificationTemplate.objects.all()
            vt_serialiser = self.serializer_class(vt_objects, many=True)
            verification_templates = vt_serialiser.data
            for verification_template in verification_templates:
                verification_template["walletName"] = datasource.name
                verification_template["walletLocation"] = datasource.location
        except VerificationTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Verification templates not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Construct the response data
        response_data = {
            "verificationTemplates": vt_serialiser.data,
        }

        return JsonResponse(response_data)


class DataSourceOpenApiUrlView(APIView):
    """
    Update the data source's OpenAPI specification URL.

    This endpoint allows data sources to configure or update their OpenAPI
    specification URL, which provides machine-readable documentation of
    the data source's API endpoints. This URL is used by the dataspace
    to understand the data source's capabilities and available data.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing data source.
    """

    serializer_class = DataSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Update the data source's OpenAPI URL.

        Sets or updates the URL pointing to the data source's OpenAPI
        specification document. This is used for API discovery and
        integration within the dataspace ecosystem.

        Request format:
            PUT with JSON body:
            {
                "dataSource": {
                    "openApiUrl": "https://datasource.com/openapi.json"
                }
            }

        Response format:
            200 OK: Returns updated data source data.
            400 Bad Request: Missing openApiUrl field or data source not found.

        Business rules:
            - The openApiUrl field is mandatory for this endpoint.
            - The URL should point to a valid OpenAPI specification.

        Returns:
            JsonResponse: Updated data source profile with OpenAPI URL.
            Response: Error if validation fails.
        """
        data = request.data.get("dataSource", {})

        # Get the DataSource instance associated with the current user
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update the fields if they are not empty
        if data.get("openApiUrl"):
            datasource.openApiUrl = data["openApiUrl"]
        else:
            return JsonResponse(
                {"error": "Missing mandatory field openApiUrl"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Save the updated DataSource instance
        datasource.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(datasource)
        return JsonResponse({"dataSource": serializer.data}, status=status.HTTP_200_OK)


class PasswordChangeView(GenericAPIView):  # type: ignore[type-arg]
    """
    Change the authenticated user's password.

    This endpoint allows users to update their account password by providing
    the new password twice for confirmation. The endpoint uses Django's
    built-in password validation to ensure security requirements are met.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.

    Request format:
        POST with JSON body:
        {
            "new_password1": "newSecurePassword123",
            "new_password2": "newSecurePassword123"
        }

    Response format:
        200 OK: {"detail": "New password has been saved."}
        400 Bad Request: Password validation errors.

    Business rules:
        - Both password fields must match.
        - Password must meet Django's password validation requirements.
        - Sensitive parameters are protected from logging.
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = (IsAuthenticated,)

    @sensitive_post_parameters_m  # type: ignore[untyped-decorator]
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle request dispatch with sensitive parameter protection.

        Marks password fields as sensitive to prevent them from being
        logged or exposed in error reports.
        """
        return cast(HttpResponse, super().dispatch(request, *args, **kwargs))

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Process password change request.

        Validates the new passwords match and meet security requirements,
        then updates the user's password.

        Returns:
            Response: Success message on password change.

        Raises:
            400 Bad Request: If validation fails (passwords don't match
            or don't meet requirements).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "New password has been saved."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AdminReset(request: Request) -> HttpResponse:
    """
    Reset all connections and verifications in the system.

    This is an administrative endpoint that deletes all Connection and
    Verification records from the database. This is typically used for
    testing or to reset the system to a clean state.

    WARNING: This is a destructive operation that cannot be undone.
    All connection and verification data will be permanently deleted.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.

    Request format:
        POST with empty body.

    Response format:
        200 OK: Reset completed successfully.
        400 Bad Request: An error occurred during reset.

    Business rules:
        - Deletes ALL Connection records (not just for the current user).
        - Deletes ALL Verification records (not just for the current user).
        - Should be used with caution in production environments.
        - Consider restricting this to admin users only.

    Returns:
        HttpResponse: Empty 200 response on success.
        HttpResponse: Error message on failure.
    """
    try:
        # Delete all connections
        Connection.objects.all().delete()

        # Delete all verifications
        Verification.objects.all().delete()

        # Return success response
        return HttpResponse(status=status.HTTP_200_OK)
    except Exception:
        return JsonResponse(
            {"error": "An error occurred while resetting."},
            status=status.HTTP_400_BAD_REQUEST,
        )
