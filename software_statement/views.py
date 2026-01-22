"""
Software Statement Views Module

This module provides API endpoints for managing Software Statement credentials
for organisations in the data space ecosystem. Software Statements are verifiable
credentials that attest to an organisation's identity and capabilities.

Business Context:
- Software Statements are SD-JWT (Selective Disclosure JWT) based credentials
- They are issued by the Data Marketplace to verified organisations
- The credential contains organisation metadata like name, location, sector
- Used for trust establishment in B2B data sharing scenarios

Key Concepts:
- SoftwareStatement: Credential instance associated with an organisation
- SoftwareStatementTemplate: Template defining the credential structure
- Credential Exchange: The process of issuing/receiving the credential
- SD-JWT: Selective Disclosure JWT format for privacy-preserving credentials
"""

import os
from typing import Any

import requests
from constance import config
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework import status as http_status
from rest_framework.request import Request
from rest_framework.views import APIView

from organisation.models import Organisation
from software_statement.models import SoftwareStatement, SoftwareStatementTemplate
from software_statement.serializers import SoftwareStatementSerializer


def _get_organisation_or_400(
    user: Any,
) -> tuple[Organisation | None, JsonResponse | None]:
    """
    Retrieve the Organisation associated with the authenticated user.

    Business Logic:
        Validates that the requesting user is an administrator of an
        Organisation. This is required for all Software Statement operations.

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
            {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
        )


class SoftwareStatementView(APIView):
    """
    API View for managing Software Statement credentials.

    Business Purpose:
        Provides endpoints for organisations to request, view, and manage
        their Software Statement credentials. These credentials serve as
        verifiable attestations of the organisation's identity and are
        essential for establishing trust in data sharing scenarios.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with an Organisation

    Workflow:
        1. Organisation configures their endpoints (holder URL, credential offer, access point)
        2. POST request initiates credential issuance from the Data Marketplace
        3. Credential is issued as SD-JWT and stored in the organisation's wallet
        4. GET retrieves the current credential status and details
        5. DELETE removes the credential from the system

    Business Rules:
        - Each organisation can have only one active Software Statement
        - Credential issuance requires proper endpoint configuration
        - The credential contains organisation metadata (name, location, sector)
    """

    serializer_class = SoftwareStatementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Retrieve the current Software Statement for the organisation.

        Business Logic:
            Fetches the Software Statement credential associated with the
            authenticated user's organisation, including its issuance status
            and credential details.

        Request:
            GET /software-statements/

        Response (200 OK):
            {
                "softwareStatement": {
                    "CredentialExchangeId": str,
                    "status": str,
                    ... (credential details)
                },
                "organisationId": str,
                "credentialExchangeId": str,
                "status": str
            }

        Response when no credential exists (200 OK):
            {
                "softwareStatement": {},
                "organisationId": "",
                "credentialExchangeId": "",
                "status": ""
            }

        Error Responses:
            - 400: Organisation not found

        Business Rules:
            - Returns empty structure if no credential has been issued
            - Status reflects the credential exchange state
        """
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            software_statement = SoftwareStatement.objects.get(
                organisationId=organisation
            )
            software_statement_serializer = self.serializer_class(software_statement)
        except SoftwareStatement.DoesNotExist:
            return JsonResponse(
                {
                    "softwareStatement": {},
                    "organisationId": "",
                    "credentialExchangeId": "",
                    "status": "",
                }
            )

        # Construct the response data
        response_data = {
            "softwareStatement": software_statement_serializer.data.get(
                "credentialHistory"
            ),
            "organisationId": software_statement_serializer.data.get("organisationId"),
            "credentialExchangeId": software_statement_serializer.data.get(
                "credentialExchangeId"
            ),
            "status": software_statement_serializer.data.get("status"),
        }

        return JsonResponse(response_data)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Request issuance of a new Software Statement credential.

        Business Logic:
            Initiates the credential issuance process with the Data Marketplace.
            The credential is issued as an SD-JWT containing organisation metadata
            and stored in the organisation's digital wallet.

        Request:
            POST /software-statements/
            No body required - uses organisation configuration

        Response (200 OK):
            {
                "softwareStatement": {
                    "CredentialExchangeId": str,
                    "status": str,
                    ... (credential details)
                },
                "organisationId": str,
                "credentialExchangeId": str,
                "status": str
            }

        Error Responses:
            - 400: Organisation not found, missing configuration, or issuance error

        Required Organisation Configuration:
            - owsBaseUrl: Organisation's wallet service base URL
            - credentialOfferEndpoint: Endpoint for receiving credential offers
            - accessPointEndpoint: Organisation's access point URL

        Business Rules:
            - All required endpoints must be configured before issuance
            - Creates or updates the existing Software Statement record
            - Credential claims include: client_uri, name, location, industry_sector,
              cover_url, logo_url, and optionally privacy_dashboard_url
            - Uses InTime issuance mode (immediate issuance)
        """
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        if organisation is None:
            return JsonResponse(
                {"error": "Organisation not found"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        ows_base_url = organisation.owsBaseUrl
        credential_offer_endpoint = organisation.credentialOfferEndpoint
        access_point_endpoint = organisation.accessPointEndpoint

        if not ows_base_url:
            return JsonResponse(
                {"error": "Holder base url not configured"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if not credential_offer_endpoint:
            return JsonResponse(
                {"error": "Credential offer endpoint not configured"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if not access_point_endpoint:
            return JsonResponse(
                {"error": "Access point endpoint not configured"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        softwareStatementTemplate = SoftwareStatementTemplate.objects.first()
        if softwareStatementTemplate is None:
            return JsonResponse(
                {"error": "Software Statement Template not found"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        credential_definition_id = softwareStatementTemplate.credentialDefinitionId
        protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
        cover_url = f"{protocol}{request.get_host()}/service/organisation/{organisation.id}/coverimage/"
        logo_url = f"{protocol}{request.get_host()}/service/organisation/{organisation.id}/logoimage/"

        claims = {
            "client_uri": organisation.accessPointEndpoint,
            "name": organisation.name,
            "location": organisation.location,
            "industry_sector": organisation.sector,
            "cover_url": cover_url,
            "logo_url": logo_url,
        }
        privacy_dashboard_url = organisation.privacyDashboardUrl
        if privacy_dashboard_url:
            claims["privacy_dashboard_url"] = privacy_dashboard_url
        payload = {
            "issuanceMode": "InTime",
            "credentialDefinitionId": credential_definition_id,
            "userPin": "",
            "credential": {"claims": claims},
            "credentialOfferEndpoint": organisation.credentialOfferEndpoint,
        }
        data_market_place_ows_url = config.DATA_MARKETPLACE_OWS_URL
        data_market_place_api_key = config.DATA_MARKETPLACE_OWS_APIKEY

        url = f"{data_market_place_ows_url}/v2/config/digital-wallet/openid/sdjwt/credential/issue"
        authorization_header = data_market_place_api_key
        try:
            response = requests.post(
                url, headers={"Authorization": authorization_header}, json=payload
            )
            response.raise_for_status()
            response = response.json()
        except requests.exceptions.RequestException as e:
            return JsonResponse(
                {"error": f"Error calling digital wallet: {str(e)}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        credential_exchange_id = response["credentialHistory"]["CredentialExchangeId"]
        status = response["credentialHistory"]["status"]
        credential_history = response["credentialHistory"]

        # Update or create software statement
        try:
            software_statement = SoftwareStatement.objects.get(
                organisationId=organisation
            )
            software_statement.credentialExchangeId = credential_exchange_id
            software_statement.status = status
            software_statement.credentialHistory = credential_history
            software_statement.save()
        except SoftwareStatement.DoesNotExist:
            software_statement = SoftwareStatement.objects.create(
                organisationId=organisation,
                credentialExchangeId=credential_exchange_id,
                status=status,
                credentialHistory=credential_history,
            )

        # Serialize the verification object
        software_statement_serializer = SoftwareStatementSerializer(software_statement)

        # Construct the response data
        response_data = {
            "softwareStatement": software_statement_serializer.data.get(
                "credentialHistory"
            ),
            "organisationId": software_statement_serializer.data.get("organisationId"),
            "credentialExchangeId": software_statement_serializer.data.get(
                "credentialExchangeId"
            ),
            "status": software_statement_serializer.data.get("status"),
        }

        return JsonResponse(response_data)

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Delete the Software Statement credential for the organisation.

        Business Logic:
            Removes the Software Statement record from the system. Note that
            this only removes the local record; it does not revoke the credential
            from the organisation's digital wallet.

        Request:
            DELETE /software-statements/

        Response:
            - 204 No Content: Software Statement successfully deleted

        Error Responses:
            - 400: Organisation not found
            - 404: Software Statement not found

        Business Rules:
            - Only the organisation's own Software Statement can be deleted
            - Deletion is permanent for the local record
            - Organisation can request a new credential after deletion
            - Does not affect the credential in the digital wallet
        """
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            software_statement = SoftwareStatement.objects.get(
                organisationId=organisation
            )
            software_statement.delete()
            return JsonResponse(
                {"message": "software statement deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except SoftwareStatement.DoesNotExist:
            return JsonResponse(
                {"error": "software statement not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
