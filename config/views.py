import os
from django.http import JsonResponse, HttpResponse
from .serializers import (
    DataSourceSerializer,
    VerificationSerializer,
    VerificationTemplateSerializer,
)
from .models import DataSource, Verification, ImageModel, VerificationTemplate
from rest_framework.views import APIView
from rest_framework import status, permissions
from onboard.serializers import DataspaceUserSerializer
from connection.models import Connection
from dataspace_backend.settings import DATA_MARKETPLACE_DW_URL, DATA_MARKETPLACE_APIKEY
import requests

# Create your views here.


def construct_cover_image_url(baseurl: str, is_public_endpoint: bool = False):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    endpoint = "/service/data-source/logoimage/" if is_public_endpoint else "/config/data-source/logoimage/"
    return f"{protocol}{baseurl}{endpoint}"


def construct_logo_image_url(baseurl: str, is_public_endpoint: bool = False):
    protocol = "https://" if os.environ.get("ENV") == "prod" else "http://"
    endpoint = "/service/data-source/logoimage/" if is_public_endpoint else "/config/data-source/logoimage/"
    return f"{protocol}{baseurl}{endpoint}"


class DataSourceView(APIView):
    serializer_class = DataSourceSerializer
    verification_serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        admin = request.user

        # Check if a DataSource with the same admin already exists
        if DataSource.objects.filter(admin=admin).exists():
            return JsonResponse(
                {"error": "A DataSource already exists for this admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data = request.data.get("dataSource", {})

        request_data["coverImageUrl"] = construct_cover_image_url(
            baseurl=request.get_host(),
            is_public_endpoint=False
        )
        request_data["logoUrl"] = construct_logo_image_url(
            baseurl=request.get_host(),
            is_public_endpoint=False
        )

        request_data["openApiUrl"] = ""

        # Create and validate the DataSource serializer
        serializer = self.serializer_class(data=request_data)
        if serializer.is_valid():

            datasource = DataSource.objects.create(
                admin=admin, **serializer.validated_data
            )

            # Serialize the created instance to match the response format
            response_serializer = self.serializer_class(datasource)
            return JsonResponse(
                {"dataSource": response_serializer.data}, status=status.HTTP_201_CREATED
            )

        return JsonResponse(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):

        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Serialize the DataSource instance
        datasource_serializer = self.serializer_class(datasource)

        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification_serializer = self.verification_serializer_class(verification)
            verification_data = verification_serializer.data
        except Verification.DoesNotExist:
            # If no Verification exists, return empty data
            verification_data = {
                "id": "",
                "dataSourceId": "",
                "presentationExchangeId": "",
                "presentationState": "",
                "presentationRecord": {},
            }

        # Construct the response data
        response_data = {
            "dataSource": datasource_serializer.data,
            "verification": verification_data,
        }

        return JsonResponse(response_data)

    def put(self, request):
        data = request.data.get("organisation", {})

        # Get the DataSource instance associated with the current user
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
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
        if data.get("sector"):
            datasource.sector = data["sector"]

        # Save the updated DataSource instance
        datasource.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(datasource)
        return JsonResponse({"dataSource": serializer.data}, status=status.HTTP_200_OK)


class DataSourceCoverImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = ImageModel.objects.get(pk=datasource.coverImageId)
        except ImageModel.DoesNotExist:
            return JsonResponse(
                {"error": "Cover image not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type="image/jpeg")

    def put(self, request):

        uploaded_image = request.FILES.get("orgimage")

        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_image:
            # Read the binary data from the uploaded image file
            image_data = uploaded_image.read()

            if datasource.coverImageId is None:
                image = ImageModel(image_data=image_data)
                datasource.coverImageId = image.id
            else:
                # Save the binary image data to the database
                image = ImageModel.objects.get(pk=datasource.coverImageId)
                image.image_data = image_data

            image.save()

            datasource.coverImageUrl = construct_cover_image_url(
                baseurl=request.get_host(),
                is_public_endpoint=True
            )

            datasource.save()

            return JsonResponse({"message": "Image uploaded successfully"})
        else:
            return JsonResponse(
                {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )


class DataSourceLogoImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = ImageModel.objects.get(pk=datasource.logoId)
        except ImageModel.DoesNotExist:
            return JsonResponse(
                {"error": "Logo image not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type="image/jpeg")

    def put(self, request):

        uploaded_image = request.FILES.get("orgimage")

        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if uploaded_image:
            # Read the binary data from the uploaded image file
            image_data = uploaded_image.read()

            if datasource.logoId is None:
                image = ImageModel(image_data=image_data)
                datasource.logoId = image.id
            else:
                # Save the binary image data to the database
                image = ImageModel.objects.get(pk=datasource.logoId)
                image.image_data = image_data

            image.save()

            datasource.logoUrl = construct_logo_image_url(
                baseurl=request.get_host(),
                is_public_endpoint=True
            )
            datasource.save()

            return JsonResponse({"message": "Image uploaded successfully"})
        else:
            return JsonResponse(
                {"error": "No image file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )


class AdminView(APIView):
    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = self.serializer_class(request.user, many=False)
        return JsonResponse(serializer.data)

    def put(self, request):
        admin = request.user
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
    serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

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

    def post(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            connection = Connection.objects.get(dataSourceId=datasource)
        except Connection.DoesNotExist:
            return JsonResponse(
                {"error": "DISP Connection not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            verificationTemplate = VerificationTemplate.objects.get(
                dataSourceId=datasource
            )
        except VerificationTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Verification template not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_agreement_id = verificationTemplate.dataAgreementId
        connection_id = connection.connectionId
        payload = {
            "connection_id": connection_id,
            "data_agreement_id": data_agreement_id,
        }
        url = (
            f"{DATA_MARKETPLACE_DW_URL}/present-proof/data-agreement-negotiation/offer"
        )
        authorization_header = DATA_MARKETPLACE_APIKEY
        response = requests.post(
            url, json=payload, headers={"Authorization": authorization_header}
        )
        try:
            response = requests.post(
                url, headers={"Authorization": authorization_header}
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
    serializer_class = VerificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            verification_templates = VerificationTemplate.objects.filter(
                dataSourceId=datasource
            )
            verification_template_serializer = self.serializer_class(
                verification_templates, many=True
            )
        except VerificationTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Verification templates not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Construct the response data
        response_data = {
            "verificationTemplates": verification_template_serializer.data,
        }

        return JsonResponse(response_data)


class DataSourceOpenApiUrlView(APIView):
    serializer_class = DataSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        data = request.data.get("dataSource", {})

        # Get the DataSource instance associated with the current user
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
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
