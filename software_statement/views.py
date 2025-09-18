
import requests
from rest_framework import permissions, status
from rest_framework import status as http_status
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from dataspace_backend.settings import (
    DATA_MARKETPLACE_OWS_URL,
    DATA_MARKETPLACE_OWS_APIKEY
)
from software_statement.serializers import SoftwareStatementSerializer
from software_statement.models import SoftwareStatement, SoftwareStatementTemplate
from organisation.models import Organisation

# Create your views here.
class SoftwareStatementView(APIView):
    serializer_class = SoftwareStatementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            software_statement = SoftwareStatement.objects.get(organisationId=organisation)
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
            "softwareStatement": software_statement_serializer.data.get("credentialHistory"),
            "organisationId": software_statement_serializer.data.get("organisationId"),
            "credentialExchangeId": software_statement_serializer.data.get("credentialExchangeId"),
            "status": software_statement_serializer.data.get("status")
        }

        return JsonResponse(response_data)

    def post(self, request):
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=http_status.HTTP_400_BAD_REQUEST
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


        try:
            softwareStatementTemplate = SoftwareStatementTemplate.objects.first()
        except SoftwareStatementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Software Statement Template not found"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        credential_definition_id = softwareStatementTemplate.credentialDefinitionId
        payload = {
            "issuanceMode": "InTime",
            "credentialDefinitionId": credential_definition_id,
            "credential": {
                "claims": {
                    "client_uri": organisation.accessPointEndpoint
                }
            },
            "credentialOfferEndpoint": organisation.credentialOfferEndpoint
        }
        
        url = (
            f"{DATA_MARKETPLACE_OWS_URL}/v2/config/digital-wallet/openid/sdjwt/credential/issue"
        )
        authorization_header = DATA_MARKETPLACE_OWS_APIKEY
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
            software_statement = SoftwareStatement.objects.get(organisationId=organisation)
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
            "softwareStatement": software_statement_serializer.data.get("credentialHistory"),
            "organisationId": software_statement_serializer.data.get("organisationId"),
            "credentialExchangeId": software_statement_serializer.data.get("credentialExchangeId"),
            "status": software_statement_serializer.data.get("status")
        }

        return JsonResponse(response_data)
    
    def delete(self, request):
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            software_statement = SoftwareStatement.objects.get(organisationId=organisation)
            software_statement.delete()
            return JsonResponse(
                {"message": "software statement deleted successfully"}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except SoftwareStatement.DoesNotExist:
            return JsonResponse(
                {"error": "software statement not found"}, 
                status=status.HTTP_404_NOT_FOUND)