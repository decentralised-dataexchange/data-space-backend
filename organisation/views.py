from __future__ import annotations

from typing import Any

import requests
from constance import config
from django.http import HttpResponse, JsonResponse
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from dataspace_backend.image_utils import (
    get_image_response,
    update_entity_image,
)
from dataspace_backend.utils import get_organisation_or_400
from organisation.models import (
    OrganisationIdentity,
    OrganisationIdentityTemplate,
)
from organisation.serializers import (
    OrganisationIdentitySerializer,
    OrganisationSerializer,
)


class OrganisationView(APIView):
    """
    Manage organisation profile information.

    This endpoint allows authenticated organisation admins to view and
    update their organisation's profile including name, description,
    location, sector, and various configuration URLs.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing organisation.
    """

    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Retrieve the current user's organisation profile.

        Returns the complete organisation profile including all settings,
        URLs, and metadata for the organisation associated with the
        authenticated admin user.

        Response format:
            {
                "organisation": {
                    "id": "uuid",
                    "name": "Organisation Name",
                    "sector": "Healthcare",
                    "location": "City, Country",
                    "description": "...",
                    "policyUrl": "...",
                    "coverImageUrl": "...",
                    "logoUrl": "...",
                    ...
                }
            }

        Returns:
            JsonResponse: Organisation profile data.
            Response: Error if user has no associated organisation.
        """
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Serialize the Organisation instance
        organisation_serializer = self.serializer_class(organisation)

        # Construct the response data
        response_data = {"organisation": organisation_serializer.data}

        return JsonResponse(response_data)

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Update the current user's organisation profile.

        Allows organisation admins to update their organisation's profile
        information. All required fields must be provided in the request.

        Request format:
            PUT with JSON body:
            {
                "organisation": {
                    "name": "Organisation Name",
                    "sector": "Healthcare",
                    "location": "City, Country",
                    "policyUrl": "https://org.com/policy",
                    "description": "Organisation description",
                    "verificationRequestURLPrefix": "https://ows.org.com",
                    "openApiUrl": "..." (optional),
                    "credentialOfferEndpoint": "..." (optional),
                    "accessPointEndpoint": "..." (optional),
                    "privacyDashboardUrl": "..." (optional)
                }
            }

        Response format:
            202 Accepted: Returns updated organisation data.
            400 Bad Request: Missing required fields or validation errors.

        Business rules:
            - All required fields (name, sector, location, policyUrl,
              description, verificationRequestURLPrefix) must be provided.
            - Optional fields are only updated if present in the request.
            - Changes take effect immediately after save.

        Returns:
            JsonResponse: Updated organisation profile data.
            Response: Error if validation fails or user has no organisation.
        """
        data = request.data.get("organisation", {})

        # Get the Organisation instance associated with the current user
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        required_fields = [
            "name",
            "sector",
            "location",
            "policyUrl",
            "description",
            "verificationRequestURLPrefix",
        ]
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update the fields if they are not empty
        if data.get("description"):
            organisation.description = data["description"]
        if data.get("location"):
            organisation.location = data["location"]
        if data.get("name"):
            organisation.name = data["name"]
        if data.get("policyUrl"):
            organisation.policyUrl = data["policyUrl"]
        if data.get("sector"):
            organisation.sector = data["sector"]
        if data.get("verificationRequestURLPrefix"):
            organisation.owsBaseUrl = data["verificationRequestURLPrefix"]
        if data.get("openApiUrl"):
            organisation.openApiUrl = data["openApiUrl"]
        if data.get("credentialOfferEndpoint"):
            organisation.credentialOfferEndpoint = data["credentialOfferEndpoint"]
        if data.get("accessPointEndpoint"):
            organisation.accessPointEndpoint = data["accessPointEndpoint"]
        if data.get("privacyDashboardUrl"):
            organisation.accessPointEndpoint = data["privacyDashboardUrl"]

        # Save the updated organisation instance
        organisation.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(organisation)
        return JsonResponse(
            {"organisation": serializer.data}, status=status.HTTP_202_ACCEPTED
        )


class OrganisationCoverImageView(APIView):
    """
    Manage the organisation's cover/banner image.

    This endpoint handles retrieval and upload of the organisation's
    cover image, which is typically displayed as a banner on the
    organisation's profile page in the dataspace portal.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing organisation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> HttpResponse | Response:
        """
        Retrieve the organisation's cover image.

        Returns the organisation's cover/banner image as binary data.
        A default image is assigned during organisation creation if
        none is uploaded.

        Response format:
            200 OK: Binary image data with appropriate content-type header.
            400 Bad Request: User has no associated organisation.
            404 Not Found: Cover image not found in storage.

        Returns:
            HttpResponse: Binary image data.
            Response: Error if organisation or image not found.
        """
        # Get the organisation instance
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Return the binary image data as the HTTP response
        return get_image_response(organisation.coverImageId, "Cover image not found")

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Upload a new cover image for the organisation.

        Replaces the organisation's current cover image with the uploaded
        file. The image is stored and a URL is generated for retrieval.

        Request format:
            PUT with multipart/form-data:
            - orgimage: The image file to upload.

        Response format:
            200 OK: Returns updated organisation data with new image URL.
            400 Bad Request: Missing image file or validation error.

        Business rules:
            - The previous cover image is replaced.
            - Image URLs are automatically updated.

        Returns:
            JsonResponse: Updated organisation data with new cover image URL.
            Response: Error if validation fails.
        """
        uploaded_image = request.FILES.get("orgimage")

        # Get the Organisation instance
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        return update_entity_image(
            request=request,
            entity=organisation,
            uploaded_image=uploaded_image,
            image_id_attr="coverImageId",
            url_attr="coverImageUrl",
            entity_type="organisation",
        )


class OrganisationLogoImageView(APIView):
    """
    Manage the organisation's logo image.

    This endpoint handles retrieval and upload of the organisation's
    logo, which is used to represent the organisation across the
    dataspace platform (e.g., in listings, headers, and cards).

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing organisation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> HttpResponse | Response:
        """
        Retrieve the organisation's logo image.

        Returns the organisation's logo as binary data. A default logo
        is assigned during organisation creation if none is uploaded.

        Response format:
            200 OK: Binary image data with appropriate content-type header.
            400 Bad Request: User has no associated organisation.
            404 Not Found: Logo image not found in storage.

        Returns:
            HttpResponse: Binary image data.
            Response: Error if organisation or image not found.
        """
        # Get the Organisation instance
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Return the binary image data as the HTTP response
        return get_image_response(organisation.logoId, "Logo image not found")

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Upload a new logo image for the organisation.

        Replaces the organisation's current logo with the uploaded file.
        The logo is stored and a URL is generated for retrieval.

        Request format:
            PUT with multipart/form-data:
            - orgimage: The logo image file to upload.

        Response format:
            200 OK: Returns updated organisation data with new logo URL.
            400 Bad Request: Missing image file or validation error.

        Business rules:
            - The previous logo is replaced.
            - Logo URLs are automatically updated.
            - Logo appears in organisation listings and profiles.

        Returns:
            JsonResponse: Updated organisation data with new logo URL.
            Response: Error if validation fails.
        """
        uploaded_image = request.FILES.get("orgimage")

        # Get the Organisation instance
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        return update_entity_image(
            request=request,
            entity=organisation,
            uploaded_image=uploaded_image,
            image_id_attr="logoId",
            url_attr="logoUrl",
            entity_type="organisation",
        )


class OrganisationIdentityView(APIView):
    """
    Manage organisation identity verification through verifiable credentials.

    This endpoint handles the organisation's identity verification process
    using the OpenID for Verifiable Credentials (OID4VC) protocol with SD-JWT.
    Organisations can initiate verification requests, check verification
    status, and delete their identity verification records.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing organisation.

    Business context:
        Organisation identity verification is a key trust mechanism in the
        dataspace. Verified organisations have proven their identity through
        a presentation of verifiable credentials, enhancing trust between
        data providers and consumers.
    """

    serializer_class = OrganisationIdentitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Retrieve the organisation's identity verification status.

        Returns the current state of the organisation's identity verification,
        including the presentation record, verification state, and whether
        the verification has been confirmed.

        Response format:
            {
                "organisationalIdentity": {...},  // Presentation record details
                "organisationId": "uuid",
                "presentationExchangeId": "string",
                "state": "verified|pending|...",
                "verified": true|false
            }

        Returns:
            JsonResponse: Verification status and details.
            JsonResponse: Empty verification data if not yet initiated.
        """
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            org_identity = OrganisationIdentity.objects.get(organisationId=organisation)
            verification_serializer = self.serializer_class(org_identity)
        except OrganisationIdentity.DoesNotExist:
            return JsonResponse(
                {
                    "organisationalIdentity": {},
                    "organisationId": "",
                    "presentationExchangeId": "",
                    "state": "",
                    "verified": False,
                }
            )

        # Construct the response data
        response_data = {
            "organisationalIdentity": verification_serializer.data.get(
                "presentationRecord"
            ),
            "organisationId": verification_serializer.data.get("organisationId"),
            "presentationExchangeId": verification_serializer.data.get(
                "presentationExchangeId"
            ),
            "state": verification_serializer.data.get("presentationState"),
            "verified": verification_serializer.data.get("isPresentationVerified"),
        }

        return JsonResponse(response_data)

    def post(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Initiate organisation identity verification.

        Starts the identity verification process by sending a verification
        request to the Data Marketplace's digital wallet service. This
        triggers an OID4VP (OpenID for Verifiable Presentations) flow using
        SD-JWT format credentials.

        The verification request is sent to the organisation's configured
        OWS (Organisation Wallet Service) URL prefix, allowing the organisation
        to present their verifiable credentials.

        Response format:
            {
                "organisationalIdentity": {...},
                "organisationId": "uuid",
                "presentationExchangeId": "string",
                "state": "request_sent|...",
                "verified": false
            }

        Business rules:
            - Organisation must have an OrganisationIdentityTemplate configured.
            - Organisation must have a valid owsBaseUrl (verification URL prefix).
            - Creates or updates the OrganisationIdentity record.
            - Communicates with external Data Marketplace OWS service.

        Returns:
            JsonResponse: Initiated verification details with exchange ID.
            JsonResponse: Error if template not found or wallet service fails.
        """
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        organisationIdentityTemplate = OrganisationIdentityTemplate.objects.first()
        if organisationIdentityTemplate is None:
            return JsonResponse(
                {"error": "Organisation identity template not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentation_definition_id = (
            organisationIdentityTemplate.presentationDefinitionId
        )
        payload = {
            "requestByReference": True,
            "presentationDefinitionId": presentation_definition_id,
            "urlPrefix": organisation.owsBaseUrl,
        }
        data_market_place_ows_url = config.DATA_MARKETPLACE_OWS_URL
        data_market_place_api_key = config.DATA_MARKETPLACE_OWS_APIKEY
        url = f"{data_market_place_ows_url}/v3/config/digital-wallet/openid/sdjwt/verification/send"
        authorization_header = data_market_place_api_key
        try:
            response = requests.post(
                url, headers={"Authorization": authorization_header}, json=payload, timeout=30
            )
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.RequestException as e:
            return JsonResponse(
                {"error": f"Error calling digital wallet: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentation_exchange_id = response["verificationHistory"][
            "presentationExchangeId"
        ]
        presentation_state = response["verificationHistory"]["status"]
        presentation_record = response["verificationHistory"]
        is_presentation_verified = response["verificationHistory"]["verified"]

        # Update or create Verification object
        try:
            identity = OrganisationIdentity.objects.get(organisationId=organisation)
            identity.presentationExchangeId = presentation_exchange_id
            identity.presentationState = presentation_state
            identity.presentationRecord = presentation_record
            identity.isPresentationVerified = is_presentation_verified
            identity.save()
        except OrganisationIdentity.DoesNotExist:
            identity = OrganisationIdentity.objects.create(
                organisationId=organisation,
                presentationExchangeId=presentation_exchange_id,
                presentationState=presentation_state,
                presentationRecord=presentation_record,
                isPresentationVerified=is_presentation_verified,
            )

        # Serialize the verification object
        verification_serializer = OrganisationIdentitySerializer(identity)

        # Construct the response data
        response_data = {
            "organisationalIdentity": verification_serializer.data.get(
                "presentationRecord"
            ),
            "organisationId": verification_serializer.data.get("organisationId"),
            "presentationExchangeId": verification_serializer.data.get(
                "presentationExchangeId"
            ),
            "state": verification_serializer.data.get("presentationState"),
            "verified": verification_serializer.data.get("isPresentationVerified"),
        }

        return JsonResponse(response_data)

    def delete(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Delete the organisation's identity verification record.

        Removes the organisation's identity verification record from the
        database. This does not revoke any issued credentials but removes
        the local verification state, allowing the organisation to
        re-initiate the verification process if needed.

        Response format:
            204 No Content: Successfully deleted.
            404 Not Found: No identity verification record exists.

        Business rules:
            - Only deletes the local verification record.
            - Organisation can re-initiate verification after deletion.
            - Does not affect the organisation's other data.

        Returns:
            JsonResponse: Success message on deletion.
            JsonResponse: Error if no identity record exists.
        """
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            org_identity = OrganisationIdentity.objects.get(organisationId=organisation)
            org_identity.delete()
            return JsonResponse(
                {"message": "Organisation identity deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except OrganisationIdentity.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation identity not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class CodeOfConductUpdateView(APIView):
    """
    Update organisation's Code of Conduct acceptance status.

    This endpoint allows organisations to record their acceptance of the
    dataspace's Code of Conduct. Accepting the Code of Conduct is typically
    a requirement for full participation in the dataspace ecosystem.

    Authentication: JWT token required.

    Permissions:
        - User must be authenticated.
        - User must be an admin of an existing organisation.
    """

    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> JsonResponse | Response:
        """
        Update the Code of Conduct acceptance status.

        Records whether the organisation has accepted the dataspace's
        Code of Conduct. This is a boolean flag that affects the
        organisation's standing in the dataspace.

        Request format:
            PUT with JSON body:
            {
                "codeOfConduct": true|false
            }

        Response format:
            202 Accepted: Returns updated organisation data.
            400 Bad Request: User has no associated organisation.

        Business rules:
            - Organisations should accept the Code of Conduct to
              participate fully in the dataspace.
            - The Code of Conduct document can be downloaded via
              the CodeOfConductView endpoint.
            - Acceptance status is visible in the organisation profile.

        Returns:
            JsonResponse: Updated organisation data with codeOfConduct status.
            Response: Error if user has no associated organisation.
        """
        data = request.data.get("codeOfConduct", False)

        # Get the Organisation instance associated with the current user
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Guard: require a verified identity before accepting the code of conduct
        if data and not OrganisationIdentity.objects.filter(
            organisationId=organisation,
            isPresentationVerified=True,
        ).exists():
            return Response(
                {"error": "Organisation identity must be verified before accepting the code of conduct"},
                status=status.HTTP_403_FORBIDDEN,
            )

        organisation.codeOfConduct = data

        # Save the updated organisation instance
        organisation.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(organisation)
        return JsonResponse(
            {"organisation": serializer.data}, status=status.HTTP_202_ACCEPTED
        )
