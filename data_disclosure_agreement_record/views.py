import requests
from rest_framework.views import View, APIView
from django.http import JsonResponse, HttpResponse
from rest_framework import status, permissions
from data_disclosure_agreement.models import (
    DataDisclosureAgreementTemplate,
)
from organisation.models import Organisation
from oAuth2Clients.models import OrganisationOAuth2Clients
from data_disclosure_agreement_record.models import DataDisclosureAgreementRecord
from django.shortcuts import get_object_or_404
from dataspace_backend.utils import paginate_queryset
from data_disclosure_agreement_record.serializers import DataDisclosureAgreementRecordSerializer, DataDisclosureAgreementRecordsSerializer


# Create your views here.
class DataDisclosureAgreementRecordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, dataDisclosureAgreementId):
        data_disclosure_agreement_id = dataDisclosureAgreementId

        try:
            dus_organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Data using service organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                status="archived"
            ).filter(
                templateId=dataDisclosureAgreementId,
                isLatestVersion=True,
            ).order_by('-createdAt').first()
        except DataDisclosureAgreementTemplate.DoesNotExist:
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
        
        try:
            dda_record = DataDisclosureAgreementRecord.objects.filter(organisationId=dus_organisation,dataDisclosureAgreementTemplateRevisionId=data_disclosure_agreement_revision_id).order_by("-updatedAt").first()
            dda_record_id = dda_record.dataDisclosureAgreementRecordId
        except DataDisclosureAgreementRecord.DoesNotExist:
            dda_record = None
            dda_record_id = None

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

        verification_request = perform_get_verification_request(
            dda_template_revision_id=data_disclosure_agreement_revision_id,
            opt_in=opt_in,
            access_token=access_token,
            get_verification_request_endpoint=get_verification_request_endpoint,
            dda_record_id=dda_record_id,
        )
        
        if isinstance(verification_request, JsonResponse):
            return verification_request
        
        verification_status = "sign" if opt_in else "unsign"

        response_data = {"verificationRequest": verification_request, "status": verification_status}
        return JsonResponse(response_data, status=status.HTTP_200_OK)


def perform_access_point_discovery(access_point_configuration):
    try:
        access_point_configuration_wellknown_url = (
            access_point_configuration + "/.well-known/access-point-configuration"
        )
        response = requests.get(url=access_point_configuration_wellknown_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error discovering access point configuration: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def perform_auth_server_discovery(auth_server):
    try:
        auth_server_wellknown_url = (
            auth_server + "/.well-known/oauth-authorization-server"
        )
        response = requests.get(url=auth_server_wellknown_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error discovering authorisation server metadata: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def fetch_access_token(token_endpoint, client_id, client_secret):
    try:
        import base64
        auth_str = f"{client_id}:{client_secret}"
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_auth_str}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"grant_type": "client_credentials"}
        response = requests.post(url=token_endpoint, headers=headers, data=data)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("access_token")

    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error getting access token: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


def perform_get_verification_request(
    dda_template_revision_id, opt_in, access_token, get_verification_request_endpoint, dda_record_id
):
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "dataDisclosureAgreementTemplateRevisionId": dda_template_revision_id,
            "optIn": opt_in,
            "autoSend": False,
        }
        if dda_record_id:
            payload["dataDisclosureAgreementRecordId"] = dda_record_id

        response = requests.post(
            url=get_verification_request_endpoint, headers=headers, json=payload
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("verificationRequest")
        
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": f"Error performing get-verification-request: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
class SignedAgreementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return DataDisclosureAgreementRecord.objects.filter(organisationId=organisation)
        except Organisation.DoesNotExist:
            return DataDisclosureAgreementRecord.objects.none()

    def get(self, request, pk):
        """Get specific record"""
        client = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = DataDisclosureAgreementRecordSerializer(client)
        response_data = {
            "dataDisclosureAgreementRecord": serializer.data
        }
        return JsonResponse(response_data)
    
class SignedAgreementsView(APIView):
   
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter clients by the authenticated user's organisation"""
        user = self.request.user
        try:
            organisation = Organisation.objects.get(admin=user)
            return DataDisclosureAgreementRecord.objects.filter(organisationId=organisation)
        except Organisation.DoesNotExist:
            return DataDisclosureAgreementRecord.objects.none()
    
    def get(self, request):
        """List all dda records"""
        # List all clients
        clients = self.get_queryset()
        serializer = DataDisclosureAgreementRecordsSerializer(clients, many=True)

        dda_records, pagination_data = paginate_queryset(serializer.data, request)
        response_data = {
            "dataDisclosureAgreementRecord": dda_records,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)