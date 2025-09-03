import os
from django.shortcuts import render
from organisation.models import Organisation
from organisation.serializers import OrganisationSerializer
from rest_framework import permissions, status
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from config.models import ImageModel

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
            "owsBaseUrl",
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
        if data.get("owsBaseUrl"):
            organisation.owsBaseUrl = data["owsBaseUrl"]
        if data.get("openApiUrl"):
            organisation.openApiUrl = data["openApiUrl"]

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
                data_source_id=str(organisation.id),
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
                data_source_id=str(organisation.id),
                is_public_endpoint=True
            )
            organisation.save()

            return JsonResponse({"message": "Image uploaded successfully"})
        else:
            return JsonResponse(
                {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )