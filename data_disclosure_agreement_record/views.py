"""
Data Disclosure Agreement Record Views Module

This module provides API endpoints for managing Data Disclosure Agreement (DDA) Records.
DDA Records represent the signed agreements between Data Using Services (DUS) and
Data Sources, tracking the consent status and verification of data sharing agreements.

Business Context:
- DUS organisations sign DDAs to gain access to data from Data Sources
- Records track the sign/unsign state of agreements
- Verification requests are generated through the Data Source's Access Point
- OAuth2 client credentials flow is used for secure API communication

Key Concepts:
- DataDisclosureAgreementRecord: A signed instance of a DDA template
- Verification Request: A request to verify/sign a DDA through the Access Point
- opt-in/opt-out: The consent state toggled when signing/unsigning agreements
"""

from __future__ import annotations

from typing import Any

import requests
from django.db.models import QuerySet
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.views import APIView

from data_disclosure_agreement.models import (
    DataDisclosureAgreementTemplate,
)
from data_disclosure_agreement_record.models import DataDisclosureAgreementRecord
from data_disclosure_agreement_record.serializers import (
    DataDisclosureAgreementRecordSerializer,
    DataDisclosureAgreementRecordsSerializer,
)
from dataspace_backend.utils import paginate_queryset
from oAuth2Clients.models import OrganisationOAuth2Clients
from organisation.models import Organisation


def _get_dus_organisation_or_400(
    user: Any,
) -> tuple[Organisation | None, JsonResponse | None]:
    """
    Retrieve the Organisation associated with the authenticated user.

    Business Logic:
        Validates that the requesting user is an administrator of an
        Organisation (Data Using Service). This is required for all
        DDA record operations.

    Args:
        user: The authenticated Django user object

    Returns:
        Tuple of (Organisation, None) on success, or (None, JsonResponse) on failure

    Business Rules:
        - User must be the admin of exactly one Organisation
        - Returns 400 error if no Organisation association exists
    """
    try:
        return Organisation.objects.get(admin=user), None
    except Organisation.DoesNotExist:
        return None, JsonResponse(
            {"error": "Data using service organisation not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DataDisclosureAgreementRecordView(APIView):
    """
    API View for initiating DDA signing/unsigning operations.

    Business Purpose:
        Enables a Data Using Service (DUS) to sign or unsign a Data Disclosure
        Agreement. This is the core consent mechanism for B2B data sharing.
        The process involves OAuth2 authentication and verification request
        generation through the Data Source's Access Point.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a DUS Organisation
        - OAuth2 client credentials are used for Access Point communication

    Workflow:
        1. Validates the DDA template exists and is active
        2. Discovers the Data Source's Access Point configuration
        3. Obtains an OAuth2 access token using client credentials
        4. Generates a verification request for signing/unsigning
        5. Returns the verification request for the DUS to process

    Business Rules:
        - Toggle behavior: If already signed, next action is unsign, and vice versa
        - Uses the latest version of the DDA template
        - Archived DDAs are excluded from signing
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Initiate a sign or unsign operation for a DDA.

        Business Logic:
            Generates a verification request that allows the DUS to sign or
            unsign the specified DDA. The operation type (sign/unsign) is
            determined automatically based on the current agreement state.

        Request:
            POST /data-disclosure-agreement-records/{dataDisclosureAgreementId}/

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA to sign/unsign

        Response (200 OK):
            {
                "verificationRequest": str,  # URL/token for verification
                "status": str  # "sign" or "unsign"
            }

        Error Responses:
            - 400: Various configuration or discovery errors including:
                - DDA not found
                - Organisation OAuth clients not configured
                - Access Point not configured
                - Missing configuration endpoints

        Business Rules:
            - If no existing record, defaults to sign (opt-in)
            - If signed, generates unsign request
            - If unsigned or pending, generates sign request
            - Uses the DDA template revision ID for precise versioning
        """
        dus_organisation, error_response = _get_dus_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement = (
                DataDisclosureAgreementTemplate.objects.exclude(status="archived")
                .filter(
                    templateId=dataDisclosureAgreementId,
                    isLatestVersion=True,
                )
                .order_by("-createdAt")
                .first()
            )
        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data_disclosure_agreement is None:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        datasource = data_disclosure_agreement.organisationId
        data_disclosure_agreement_revision_id = (
            data_disclosure_agreement.dataDisclosureAgreementTemplateRevisionId
        )

        if not data_disclosure_agreement_revision_id:
            return JsonResponse(
                {"error": "Data disclosure agreement revision id not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ds_organisation = Organisation.objects.get(pk=datasource.id)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        organisation_oauth_client = OrganisationOAuth2Clients.objects.filter(
            organisation=ds_organisation
        ).first()

        if not organisation_oauth_client:
            return JsonResponse(
                {"error": "Organisation OAuth clients are not configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_point_configuration_endpoint = ds_organisation.accessPointEndpoint

        if not access_point_configuration_endpoint:
            return JsonResponse(
                {"error": "Data source has not configured access point configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_point_discovery_resp = perform_access_point_discovery(
            access_point_configuration_endpoint
        )

        if isinstance(access_point_discovery_resp, JsonResponse):
            return access_point_discovery_resp

        get_verification_request_endpoint = access_point_discovery_resp.get(
            "get_verification_request_endpoint"
        )
        if not get_verification_request_endpoint:
            return JsonResponse(
                {
                    "error": "get_verification_request_endpoint is missing in access point configuration"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        auth_server = access_point_discovery_resp.get("authorization_server")
        if not auth_server:
            return JsonResponse(
                {
                    "error": "authorization_server is missing in access point configuration"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        auth_server_metadata = perform_auth_server_discovery(auth_server=auth_server)
        if isinstance(auth_server_metadata, JsonResponse):
            return auth_server_metadata

        token_endpoint = auth_server_metadata.get("token_endpoint")
        if not token_endpoint:
            return JsonResponse(
                {"error": "token_endpoint is missing in access point configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_id = organisation_oauth_client.client_id
        client_secret = organisation_oauth_client.client_secret

        access_token = fetch_access_token(
            token_endpoint=token_endpoint,
            client_id=client_id,
            client_secret=client_secret,
        )

        if isinstance(access_token, JsonResponse):
            return access_token

        if access_token is None:
            return JsonResponse(
                {"error": "Failed to retrieve access token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dda_record_id = None
        try:
            dda_record = (
                DataDisclosureAgreementRecord.objects.filter(
                    organisationId=dus_organisation,
                    dataDisclosureAgreementTemplateRevisionId=data_disclosure_agreement_revision_id,
                )
                .order_by("-updatedAt")
                .first()
            )
            if dda_record:
                dda_record_id = dda_record.dataDisclosureAgreementRecordId
        except DataDisclosureAgreementRecord.DoesNotExist:
            dda_record = None

        opt_in: bool = True
        if dda_record:
            state = dda_record.state
            saved_opt_in = dda_record.optIn
            if state != "signed":
                opt_in = saved_opt_in
            else:
                opt_in = not saved_opt_in
        else:
            opt_in = True

        url_prefix = dus_organisation.owsBaseUrl if dus_organisation else None
        verification_request = perform_get_verification_request(
            dda_template_revision_id=data_disclosure_agreement_revision_id,
            opt_in=opt_in,
            access_token=access_token,
            get_verification_request_endpoint=get_verification_request_endpoint,
            dda_record_id=dda_record_id,
            url_prefix=url_prefix,
        )

        if isinstance(verification_request, JsonResponse):
            return verification_request

        verification_status = "sign" if opt_in else "unsign"

        response_data = {
            "verificationRequest": verification_request,
            "status": verification_status,
        }
        return JsonResponse(response_data, status=status.HTTP_200_OK)


class DataDisclosureAgreementRecordSignInStatusView(APIView):
    """
    API View for checking the current sign-in status of a DDA.

    Business Purpose:
        Allows a Data Using Service to query the current consent status
        for a specific DDA. This is useful for UI rendering and determining
        what action (sign/unsign) should be presented to the user.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a DUS Organisation

    Business Rules:
        - Returns 'sign' if the next action would be to sign (no record or unsigned)
        - Returns 'unsign' if the next action would be to unsign (currently signed)
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Get the current sign status for a DDA.

        Business Logic:
            Determines what the next consent action would be for this DDA.
            This helps the UI display the appropriate action button.

        Request:
            GET /data-disclosure-agreement-records/{dataDisclosureAgreementId}/status/

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response (200 OK):
            {
                "status": str  # "sign" or "unsign"
            }

        Error Responses:
            - 400: DDA not found or Organisation not found

        Business Rules:
            - 'sign' status: No existing record OR existing record not in 'signed' state
            - 'unsign' status: Existing record is in 'signed' state
            - Uses the latest DDA template revision for lookup
        """
        dus_organisation, error_response = _get_dus_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement = (
                DataDisclosureAgreementTemplate.objects.exclude(status="archived")
                .filter(
                    templateId=dataDisclosureAgreementId,
                    isLatestVersion=True,
                )
                .order_by("-createdAt")
                .first()
            )
        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data_disclosure_agreement is None:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_disclosure_agreement_revision_id = (
            data_disclosure_agreement.dataDisclosureAgreementTemplateRevisionId
        )

        if not data_disclosure_agreement_revision_id:
            return JsonResponse(
                {"error": "Data disclosure agreement revision id not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dda_record = (
                DataDisclosureAgreementRecord.objects.filter(
                    organisationId=dus_organisation,
                    dataDisclosureAgreementTemplateRevisionId=data_disclosure_agreement_revision_id,
                )
                .order_by("-updatedAt")
                .first()
            )
        except DataDisclosureAgreementRecord.DoesNotExist:
            dda_record = None

        opt_in: bool = True
        if dda_record:
            state = dda_record.state
            saved_opt_in = dda_record.optIn
            if state != "signed":
                opt_in = saved_opt_in
            else:
                opt_in = not saved_opt_in
        else:
            opt_in = True

        verification_status = "sign" if opt_in else "unsign"

        response_data = {"status": verification_status}
        return JsonResponse(response_data, status=status.HTTP_200_OK)


def perform_access_point_discovery(
    access_point_configuration: str,
) -> dict[str, Any] | JsonResponse:
    """
    Discover the Access Point configuration from the Data Source.

    Business Logic:
        Fetches the well-known Access Point configuration document from
        the Data Source. This document contains endpoints needed for
        OAuth2 authorization and verification request generation.

    Args:
        access_point_configuration: Base URL of the Access Point

    Returns:
        dict containing Access Point configuration on success,
        JsonResponse with error on failure

    Business Rules:
        - Uses .well-known/access-point-configuration endpoint
        - Configuration must include authorization_server and
          get_verification_request_endpoint
    """
    try:
        access_point_configuration_wellknown_url = (
            access_point_configuration + "/.well-known/access-point-configuration"
        )
        response = requests.get(url=access_point_configuration_wellknown_url, timeout=30)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error discovering access point configuration: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def perform_auth_server_discovery(auth_server: str) -> dict[str, Any] | JsonResponse:
    """
    Discover the OAuth2 Authorization Server metadata.

    Business Logic:
        Fetches the OAuth2 Authorization Server metadata document using
        the standard .well-known endpoint. This provides the token endpoint
        needed for obtaining access tokens.

    Args:
        auth_server: Base URL of the OAuth2 Authorization Server

    Returns:
        dict containing auth server metadata on success,
        JsonResponse with error on failure

    Business Rules:
        - Uses .well-known/oauth-authorization-server endpoint (RFC 8414)
        - Metadata must include token_endpoint for client credentials flow
    """
    try:
        auth_server_wellknown_url = (
            auth_server + "/.well-known/oauth-authorization-server"
        )
        response = requests.get(url=auth_server_wellknown_url, timeout=30)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error discovering authorisation server metadata: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def fetch_access_token(
    token_endpoint: str, client_id: str, client_secret: str
) -> str | None | JsonResponse:
    """
    Obtain an OAuth2 access token using client credentials grant.

    Business Logic:
        Authenticates the DUS organisation with the Data Source's OAuth2
        server using the client credentials flow. The obtained access
        token is used to authorize verification request API calls.

    Args:
        token_endpoint: OAuth2 token endpoint URL
        client_id: OAuth2 client ID for the DUS organisation
        client_secret: OAuth2 client secret for the DUS organisation

    Returns:
        str access token on success, None if token not in response,
        JsonResponse with error on failure

    Business Rules:
        - Uses HTTP Basic authentication for client credentials
        - Grant type is always 'client_credentials'
        - Token is used for Access Point API authorization
    """
    try:
        import base64

        auth_str = f"{client_id}:{client_secret}"
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_auth_str}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials"}
        response = requests.post(url=token_endpoint, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        response_data: dict[str, Any] = response.json()
        token: str | None = response_data.get("access_token")
        return token

    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error getting access token: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def perform_get_verification_request(
    dda_template_revision_id: str,
    opt_in: bool,
    access_token: str,
    get_verification_request_endpoint: str,
    dda_record_id: str | None,
    url_prefix: str | None,
) -> str | None | JsonResponse:
    """
    Generate a verification request from the Data Source's Access Point.

    Business Logic:
        Calls the Data Source's Access Point to generate a verification
        request for signing or unsigning a DDA. The verification request
        is then used by the DUS to complete the consent process.

    Args:
        dda_template_revision_id: Unique identifier for the DDA template revision
        opt_in: True for sign operation, False for unsign operation
        access_token: OAuth2 bearer token for authorization
        get_verification_request_endpoint: Access Point endpoint URL
        dda_record_id: Existing record ID (for updates/unsign operations)
        url_prefix: URL prefix for callback/redirect URLs

    Returns:
        str verification request token/URL on success,
        None if not in response, JsonResponse with error on failure

    Business Rules:
        - autoSend is always False (manual verification required)
        - dda_record_id is included for update operations
        - url_prefix configures callback URLs for the DUS
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "dataDisclosureAgreementTemplateRevisionId": dda_template_revision_id,
            "optIn": opt_in,
            "autoSend": False,
        }
        if dda_record_id:
            payload["dataDisclosureAgreementRecordId"] = dda_record_id
        if url_prefix:
            payload["urlPrefix"] = url_prefix

        response = requests.post(
            url=get_verification_request_endpoint, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        response_data: dict[str, Any] = response.json()
        verification_request: str | None = response_data.get("verificationRequest")
        return verification_request

    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error performing get-verification-request: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class SignedAgreementView(APIView):
    """
    API View for managing individual signed DDA records.

    Business Purpose:
        Provides CRUD operations for signed agreement records. These records
        represent the consent state between a DUS and Data Source, tracking
        the signing history and current status of data sharing agreements.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with an Organisation

    Business Rules:
        - Only records belonging to the user's organisation are accessible
        - Records are scoped to prevent cross-organisation access
        - Deletion removes the consent record permanently
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[DataDisclosureAgreementRecord]:
        """
        Filter DDA records by the authenticated user's organisation.

        Business Logic:
            Ensures data isolation by only returning records that belong
            to the requesting user's organisation.

        Returns:
            QuerySet of DataDisclosureAgreementRecord filtered by organisation,
            or empty QuerySet if organisation not found
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return DataDisclosureAgreementRecord.objects.filter(
                organisationId=organisation
            )
        except Organisation.DoesNotExist:
            return DataDisclosureAgreementRecord.objects.none()

    def get(self, request: Request, pk: str, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Retrieve a specific signed agreement record.

        Business Logic:
            Fetches the complete details of a specific DDA record including
            its current state, signing history, and associated template info.

        Request:
            GET /signed-agreements/{pk}/

        Path Parameters:
            - pk (str): Primary key of the DDA record

        Response (200 OK):
            {
                "dataDisclosureAgreementRecord": {
                    ... (full record details)
                }
            }

        Error Responses:
            - 404: Record not found or access denied
        """
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = DataDisclosureAgreementRecordSerializer(client)
        response_data = {"dataDisclosureAgreementRecord": serializer.data}
        return JsonResponse(response_data)

    def delete(
        self, request: Request, pk: str, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """
        Delete a specific signed agreement record.

        Business Logic:
            Permanently removes a DDA record. This effectively revokes
            the consent for that specific agreement version.

        Request:
            DELETE /signed-agreements/{pk}/

        Path Parameters:
            - pk (str): Primary key of the DDA record to delete

        Response:
            - 204 No Content: Record successfully deleted

        Error Responses:
            - 404: Record not found or access denied

        Business Rules:
            - Only the organisation's own records can be deleted
            - Deletion is permanent and cannot be undone
        """
        record = get_object_or_404(self.get_queryset(), pk=pk)
        record.delete()
        return JsonResponse(
            {"message": "Data disclosure agreement record deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class SignedAgreementsView(APIView):
    """
    API View for listing all signed DDA records for an organisation.

    Business Purpose:
        Provides a paginated list of all signed agreements for a DUS
        organisation. This allows administrators to view and manage
        all their data sharing consents in one place.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with an Organisation

    Business Rules:
        - Only records belonging to the user's organisation are returned
        - Records are sorted by update date (most recent first)
        - Results are paginated for performance
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[DataDisclosureAgreementRecord]:
        """
        Filter DDA records by the authenticated user's organisation.

        Business Logic:
            Ensures data isolation and returns records sorted by
            most recently updated first for better UX.

        Returns:
            QuerySet of DataDisclosureAgreementRecord filtered by organisation
            and sorted by updatedAt descending, or empty QuerySet if
            organisation not found
        """
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return DataDisclosureAgreementRecord.objects.filter(
                organisationId=organisation
            ).order_by("-updatedAt")
        except Organisation.DoesNotExist:
            return DataDisclosureAgreementRecord.objects.none()

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all signed agreement records for the organisation.

        Business Logic:
            Retrieves all DDA records for the authenticated user's
            organisation with pagination support.

        Request:
            GET /signed-agreements/
            Query Parameters:
                - page (int): Page number for pagination
                - limit (int): Number of items per page

        Response (200 OK):
            {
                "dataDisclosureAgreementRecord": [...],
                "pagination": {
                    "currentPage": int,
                    "totalItems": int,
                    "totalPages": int,
                    "limit": int,
                    "hasPrevious": bool,
                    "hasNext": bool
                }
            }

        Business Rules:
            - Records are sorted by updatedAt descending
            - Only organisation's own records are included
        """
        # List all clients
        clients = self.get_queryset()
        serializer = DataDisclosureAgreementRecordsSerializer(clients, many=True)

        dda_records, pagination_data = paginate_queryset(list(serializer.data), request)
        response_data = {
            "dataDisclosureAgreementRecord": dda_records,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)
