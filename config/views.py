from django.http import JsonResponse, HttpResponse
from .serializers import DataSourceSerializer, VerificationSerializer, VerificationTemplateSerializer
from .models import DataSource, Verification, ImageModel, VerificationTemplate
from rest_framework.views import APIView
from rest_framework import status, permissions
from onboard.serializers import DataspaceUserSerializer
from uuid import uuid4

# Create your views here.


class DataSourceView(APIView):
    serializer_class = DataSourceSerializer
    verification_serializer_class = VerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        admin = request.user

        # Check if a DataSource with the same admin already exists
        if DataSource.objects.filter(admin=admin).exists():
            return JsonResponse({'error': 'A DataSource already exists for this admin'}, status=status.HTTP_400_BAD_REQUEST)

        request_data = request.data.get("dataSource", {})

        request_data["coverImageUrl"] = "https://" + \
            request.get_host() + "/config/data-source/coverimage/"
        request_data["logoUrl"] = "https://" + \
            request.get_host() + "/config/data-source/logoimage/"
        
        request_data["openApiUrl"] = ""

        # Create and validate the DataSource serializer
        serializer = self.serializer_class(data=request_data)
        if serializer.is_valid():

            datasource = DataSource.objects.create(
                admin=admin, **serializer.validated_data)

            # Serialize the created instance to match the response format
            response_serializer = self.serializer_class(datasource)
            return JsonResponse({'dataSource': response_serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the DataSource instance
        datasource_serializer = self.serializer_class(datasource)

        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification_serializer = self.verification_serializer_class(
                verification)
            verification_data = verification_serializer.data
        except Verification.DoesNotExist:
            # If no Verification exists, return empty data
            verification_data = {
                'id': '',
                'dataSourceId': '',
                'presentationExchangeId': '',
                'presentationState': '',
                'presentationRecord': {},
            }

        # Construct the response data
        response_data = {
            'dataSource': datasource_serializer.data,
            'verification': verification_data,
        }

        return JsonResponse(response_data)

    def put(self, request):
        data = request.data.get('organisation', {})

        # Get the DataSource instance associated with the current user
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the fields if they are not empty
        if data.get('description'):
            datasource.description = data['description']
        if data.get('location'):
            datasource.location = data['location']
        if data.get('name'):
            datasource.name = data['name']
        if data.get('policyUrl'):
            datasource.policyUrl = data['policyUrl']
        if data.get('sector'):
            datasource.sector = data['sector']

        # Save the updated DataSource instance
        datasource.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(datasource)
        return JsonResponse({'dataSource': serializer.data}, status=status.HTTP_200_OK)


class DataSourceCoverImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = ImageModel.objects.get(pk=datasource.coverImageId)
        except ImageModel.DoesNotExist:
            return JsonResponse({'error': 'Cover image not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type='image/jpeg')

    def put(self, request):

        uploaded_image = request.FILES.get('orgimage')

        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

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

            datasource.coverImageUrl = "https://" + \
                request.get_host() + "/service/data-source/" + datasource.id + "/coverimage"

            datasource.save()

            return JsonResponse({'message': 'Image uploaded successfully'})
        else:
            return JsonResponse({'error': 'No image file uploaded'}, status=status.HTTP_400_BAD_REQUEST)


class DataSourceLogoImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = ImageModel.objects.get(pk=datasource.logoId)
        except ImageModel.DoesNotExist:
            return JsonResponse({'error': 'Logo image not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type='image/jpeg')

    def put(self, request):

        uploaded_image = request.FILES.get('orgimage')

        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

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

            datasource.logoUrl = "https://" + \
                request.get_host() + "/service/data-source/" + datasource.id + "/logoimage"
            datasource.save()

            return JsonResponse({'message': 'Image uploaded successfully'})
        else:
            return JsonResponse({'error': 'No image file uploaded'}, status=status.HTTP_400_BAD_REQUEST)


class AdminView(APIView):
    serializer_class = DataspaceUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = self.serializer_class(request.user, many=False)
        return JsonResponse(serializer.data)

    def put(self, request):
        admin = request.user
        request_data = request.data
        if 'name' not in request_data:
            return JsonResponse({'error': 'Name field is required'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(
            admin, data=request_data, partial=True)
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
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification_serializer = self.serializer_class(
                verification)
        except Verification.DoesNotExist:
            return JsonResponse({'error': 'Data source verification not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Construct the response data
        response_data = {
            'verification': verification_serializer.data,
        }

        return JsonResponse(response_data)

    def post(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Add dummy presentation
        presentation_exchange_id = str(uuid4())

        response = {
            "verificationHistory": {
                "id": "6603e82d8b3a694e41bf774a",
                "autoPresent": False,
                "connectionId": "4e0ca9c3-2537-46bb-8fd8-90868953f3ad",
                "createdAt": "2024-03-27 09:34:37.016226Z",
                "errorMsg": "",
                "initiator": "self",
                "presentationExchangeId": presentation_exchange_id,
                "presentationRequest": {
                    "name": "parking verify 1",
                    "version": "2.0.0",
                    "requestedAttributes": {
                        "additionalProp1": {
                            "name": "Car name",
                            "restrictions": []
                        },
                        "additionalProp2": {
                            "name": "Number",
                            "restrictions": []
                        }
                    },
                    "requestedPredicates": {},
                    "nonce": "32417908491254422565941"
                },
                "role": "verifier",
                "state": "request_sent",
                "threadId": "84d0caa4-9fc8-43e9-96d8-514826538b09",
                "trace": False,
                "updatedAt": "2024-03-27 09:34:37.068448Z",
                "verified": False,
                "dataAgreementId": "87888023-350d-49e6-8c39-4cfe76635823",
                "dataAgreementTemplateId": "e4eadd72-8f58-4be8-904a-d6c119ca2f00",
                "dataAgreementStatus": "offer",
                "dataAgreementProblemReport": ""
            }
        }
        presentation_record = response['verificationHistory']

        # Update or create Verification object
        try:
            verification = Verification.objects.get(dataSourceId=datasource)
            verification.presentationExchangeId = presentation_exchange_id
            verification.presentationState = "request_sent"
            verification.presentationRecord = presentation_record
            verification.save()
        except Verification.DoesNotExist:
            verification = Verification.objects.create(
                dataSourceId=datasource,
                presentationExchangeId=presentation_exchange_id,
                presentationState="request_sent",
                presentationRecord=presentation_record
            )

        # Serialize the verification object
        verification_serializer = VerificationSerializer(verification)

        # Construct the response data
        response_data = {
            'verification': verification_serializer.data,
        }

        return JsonResponse(response_data)


class VerificationTemplateView(APIView):
    serializer_class = VerificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification_templates = VerificationTemplate.objects.filter(dataSourceId=datasource)
            verification_template_serializer = self.serializer_class(
                verification_templates, many=True)
        except VerificationTemplate.DoesNotExist:
            return JsonResponse({'error': 'Verification templates not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Construct the response data
        response_data = {
            'verificationTemplates': verification_template_serializer.data,
        }

        return JsonResponse(response_data)
    
class DataSourceOpenApiUrlView(APIView):
    serializer_class = DataSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        data = request.data.get('dataSource', {})

        # Get the DataSource instance associated with the current user
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the fields if they are not empty
        if data.get('openApiUrl'):
            datasource.openApiUrl = data['openApiUrl']
        else:
            return JsonResponse({'error': 'Missing mandatory field openApiUrl'}, status=status.HTTP_400_BAD_REQUEST)
        # Save the updated DataSource instance
        datasource.save()

        # Serialize the updated DataSource instance
        serializer = self.serializer_class(datasource)
        return JsonResponse({'dataSource': serializer.data}, status=status.HTTP_200_OK)



