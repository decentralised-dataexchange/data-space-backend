import os
import requests
from django.shortcuts import render
from organisation.models import Organisation, OrganisationIdentity, OrganisationIdentityTemplate
from organisation.serializers import OrganisationSerializer, OrganisationIdentitySerializer, OrganisationIdentityTemplateSerializer
from rest_framework import permissions, status
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from config.models import ImageModel
from constance import config

# Create your views here.
class OrganisationView(APIView):
    serializer_class = OrganisationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

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
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        
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

        # Save the updated organisation instance
        organisation.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(organisation)
        return JsonResponse({"organisation": serializer.data}, status=status.HTTP_202_ACCEPTED)
    
def construct_cover_image_url(
    baseurl: str,
    organisation_id: str,
    is_public_endpoint: bool = False
):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/organisation/{organisation_id}/coverimage/"
    return f"{protocol}{baseurl}{endpoint}"


def construct_logo_image_url(
    baseurl: str,
    organisation_id: str,
    is_public_endpoint: bool = False
):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    url_prefix = "service" if is_public_endpoint else "config"
    endpoint = f"/{url_prefix}/organisation/{organisation_id}/logoimage/"
    return f"{protocol}{baseurl}{endpoint}"
    
class OrganisationCoverImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get the organisation instance
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = ImageModel.objects.get(pk=organisation.coverImageId)
        except ImageModel.DoesNotExist:
            return JsonResponse(
                {"error": "Cover image not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type="image/jpeg")

    def put(self, request):

        uploaded_image = request.FILES.get("orgimage")

        try:
            # Get the Organisation instance
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_image:
            # Read the binary data from the uploaded image file
            image_data = uploaded_image.read()

            if organisation.coverImageId is None:
                image = ImageModel(image_data=image_data)
                organisation.coverImageId = image.id
            else:
                # Save the binary image data to the database
                image = ImageModel.objects.get(pk=organisation.coverImageId)
                image.image_data = image_data

            image.save()

            organisation.coverImageUrl = construct_cover_image_url(
                baseurl=request.get_host(),
                organisation_id=str(organisation.id),
                is_public_endpoint=True
            )

            organisation.save()

            return JsonResponse({"message": "Image uploaded successfully"})
        else:
            return JsonResponse(
                {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

class OrganisationLogoImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get the Organisation instance
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = ImageModel.objects.get(pk=organisation.logoId)
        except ImageModel.DoesNotExist:
            return JsonResponse(
                {"error": "Logo image not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type="image/jpeg")

    def put(self, request):

        uploaded_image = request.FILES.get("orgimage")

        try:
            # Get the Organisation instance
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_image:
            # Read the binary data from the uploaded image file
            image_data = uploaded_image.read()

            if organisation.logoId is None:
                image = ImageModel(image_data=image_data)
                organisation.logoId = image.id
            else:
                # Save the binary image data to the database
                image = ImageModel.objects.get(pk=organisation.logoId)
                image.image_data = image_data

            image.save()

            organisation.logoUrl = construct_logo_image_url(
                baseurl=request.get_host(),
                organisation_id=str(organisation.id),
                is_public_endpoint=True
            )
            organisation.save()

            return JsonResponse({"message": "Image uploaded successfully"})
        else:
            return JsonResponse(
                {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

class OrganisationIdentityView(APIView):
    serializer_class = OrganisationIdentitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

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
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )


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
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

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