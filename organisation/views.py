import os
import requests
from organisation.models import Organisation, OrganisationIdentity, OrganisationIdentityTemplate
from organisation.serializers import OrganisationSerializer, OrganisationIdentitySerializer, OrganisationIdentityTemplateSerializer
from rest_framework import permissions, status
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from config.models import ImageModel
from constance import config

# Create your views here.
def _get_organisation_or_400(user):
    try:
        return Organisation.objects.get(admin=user), None
    except Organisation.DoesNotExist:
        return None, JsonResponse(
            {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
        )


class OrganisationView(APIView):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Serialize the Organisation instance
        organisation_serializer = self.serializer_class(organisation)

        # Construct the response data
        response_data = {
            "organisation": organisation_serializer.data
        }

        return JsonResponse(response_data)

    def put(self, request):
        data = request.data.get("organisation", {})

        # Get the Organisation instance associated with the current user
        organisation, error_response = _get_organisation_or_400(request.user)
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
        return JsonResponse({"organisation": serializer.data}, status=status.HTTP_202_ACCEPTED)
    
def _construct_image_url(
    baseurl: str,
    organisation_id: str,
    image_endpoint: str,
    is_public_endpoint: bool = False,
):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/organisation/{organisation_id}/{image_endpoint}/"
    return f"{protocol}{baseurl}{endpoint}"


def construct_cover_image_url(
    baseurl: str,
    organisation_id: str,
    is_public_endpoint: bool = False
):
    return _construct_image_url(
        baseurl=baseurl,
        organisation_id=organisation_id,
        image_endpoint="coverimage",
        is_public_endpoint=is_public_endpoint,
    )


def construct_logo_image_url(
    baseurl: str,
    organisation_id: str,
    is_public_endpoint: bool = False
):
    return _construct_image_url(
        baseurl=baseurl,
        organisation_id=organisation_id,
        image_endpoint="logoimage",
        is_public_endpoint=is_public_endpoint,
    )


def _get_image_response(image_id, missing_error_message: str):
    try:
        image = ImageModel.objects.get(pk=image_id)
    except ImageModel.DoesNotExist:
        return JsonResponse(
            {"error": missing_error_message}, status=status.HTTP_400_BAD_REQUEST
        )

    return HttpResponse(image.image_data, content_type="image/jpeg")


def _update_organisation_image(
    request,
    organisation,
    uploaded_image,
    image_id_attr: str,
    url_attr: str,
    url_builder,
):
    if not uploaded_image:
        return JsonResponse(
            {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
        )

    image_data = uploaded_image.read()
    image_id = getattr(organisation, image_id_attr)

    if image_id is None:
        image = ImageModel(image_data=image_data)
        setattr(organisation, image_id_attr, image.id)
    else:
        image = ImageModel.objects.get(pk=image_id)
        image.image_data = image_data

    image.save()

    setattr(
        organisation,
        url_attr,
        url_builder(
            baseurl=request.get_host(),
            organisation_id=str(organisation.id),
            is_public_endpoint=True,
        ),
    )

    organisation.save()
    return JsonResponse({"message": "Image uploaded successfully"})
    
class OrganisationCoverImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the organisation instance
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Return the binary image data as the HTTP response
        return _get_image_response(organisation.coverImageId, "Cover image not found")

    def put(self, request):

        uploaded_image = request.FILES.get("orgimage")

        # Get the Organisation instance
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        return _update_organisation_image(
            request=request,
            organisation=organisation,
            uploaded_image=uploaded_image,
            image_id_attr="coverImageId",
            url_attr="coverImageUrl",
            url_builder=construct_cover_image_url,
        )

class OrganisationLogoImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the Organisation instance
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        # Return the binary image data as the HTTP response
        return _get_image_response(organisation.logoId, "Logo image not found")

    def put(self, request):

        uploaded_image = request.FILES.get("orgimage")

        # Get the Organisation instance
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        return _update_organisation_image(
            request=request,
            organisation=organisation,
            uploaded_image=uploaded_image,
            image_id_attr="logoId",
            url_attr="logoUrl",
            url_builder=construct_logo_image_url,
        )

class OrganisationIdentityView(APIView):
    serializer_class = OrganisationIdentitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        organisation, error_response = _get_organisation_or_400(request.user)
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
                    "verified": False
                }
            )

        # Construct the response data
        response_data = {
            "organisationalIdentity": verification_serializer.data.get("presentationRecord"),
            "organisationId": verification_serializer.data.get("organisationId"),
            "presentationExchangeId": verification_serializer.data.get("presentationExchangeId"),
            "state": verification_serializer.data.get("presentationState"),
            "verified": verification_serializer.data.get("isPresentationVerified")
        }

        return JsonResponse(response_data)

    def post(self, request):
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response


        try:
            organisationIdentityTemplate = OrganisationIdentityTemplate.objects.first()
        except OrganisationIdentityTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation identity template not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentation_definition_id = organisationIdentityTemplate.presentationDefinitionId
        payload = {
            "requestByReference": True,
            "presentationDefinitionId": presentation_definition_id,
            "urlPrefix": organisation.owsBaseUrl
        }
        data_market_place_ows_url = config.DATA_MARKETPLACE_OWS_URL
        data_market_place_api_key = config.DATA_MARKETPLACE_OWS_APIKEY
        url = (
            f"{data_market_place_ows_url}/v3/config/digital-wallet/openid/sdjwt/verification/send"
        )
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
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentation_exchange_id = response["verificationHistory"]["presentationExchangeId"]
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
                isPresentationVerified = is_presentation_verified
            )

        # Serialize the verification object
        verification_serializer = OrganisationIdentitySerializer(identity)

        # Construct the response data
        response_data = {
            "organisationalIdentity": verification_serializer.data.get("presentationRecord"),
            "organisationId": verification_serializer.data.get("organisationId"),
            "presentationExchangeId": verification_serializer.data.get("presentationExchangeId"),
            "state": verification_serializer.data.get("presentationState"),
            "verified": verification_serializer.data.get("isPresentationVerified")
        }

        return JsonResponse(response_data)

    def delete(self, request):
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            org_identity = OrganisationIdentity.objects.get(organisationId=organisation)
            org_identity.delete()
            return JsonResponse(
                {"message": "Organisation identity deleted successfully"}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except OrganisationIdentity.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation identity not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
class CodeOfConductUpdateView(APIView):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        data = request.data.get("codeOfConduct", False)

        # Get the Organisation instance associated with the current user
        organisation, error_response = _get_organisation_or_400(request.user)
        if error_response:
            return error_response
        
        organisation.codeOfConduct = data
        
        # Save the updated organisation instance
        organisation.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(organisation)
        return JsonResponse({"organisation": serializer.data}, status=status.HTTP_202_ACCEPTED)
