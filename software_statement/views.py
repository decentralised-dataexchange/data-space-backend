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


# Create your views here.
def _get_organisation_or_400(
    user: Any,
) -> tuple[Organisation | None, JsonResponse | None]:
    try:
        return Organisation.objects.get(admin=user), None
    except Organisation.DoesNotExist:
        return None, JsonResponse(
            {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
        )


class SoftwareStatementView(APIView):
    serializer_class = SoftwareStatementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
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
