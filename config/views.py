from django.http import JsonResponse, HttpResponse
from .serializers import DataSourceSerializer, VerificationSerializer
from .models import DataSource, Verification, ImageModel
from rest_framework.views import APIView
from rest_framework import status, permissions

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

        request_data = request.data.get("organisation", {})

        request_data["coverImageUrl"] = "https://" + \
            request.get_host() + "/config/data-source/coverimage/"
        request_data["logoUrl"] = "https://" + \
            request.get_host() + "/config/data-source/logoimage/"

        # Create and validate the DataSource serializer
        serializer = self.serializer_class(data=request_data)
        if serializer.is_valid():

            datasource = DataSource.objects.create(
                admin=admin, **serializer.validated_data)

            # Serialize the created instance to match the response format
            response_serializer = self.serializer_class(datasource)
            return JsonResponse({'organisation': response_serializer.data}, status=status.HTTP_201_CREATED)

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
        return JsonResponse({'organisation': serializer.data}, status=status.HTTP_200_OK)


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
                request.get_host() + "/config/data-source/coverimage/"

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
                request.get_host() + "/config/data-source/logoimage/"
            datasource.save()

            return JsonResponse({'message': 'Image uploaded successfully'})
        else:
            return JsonResponse({'error': 'No image file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
