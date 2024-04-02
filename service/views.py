from django.shortcuts import render
from rest_framework.views import View
from config.models import DataSource, ImageModel, Verification
from config.serializers import VerificationSerializer, DataSourceSerializer
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from data_disclosure_agreement.models import DataDisclosureAgreement
from data_disclosure_agreement.serializers import DataDisclosureAgreementsSerializer
from dataspace_backend.utils import paginate_queryset


# Create your views here.


class DataSourceCoverImageView(View):

    def get(self, request, dataSourceId):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(pk=dataSourceId)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = ImageModel.objects.get(pk=datasource.coverImageId)
        except ImageModel.DoesNotExist:
            return JsonResponse({'error': 'Cover image not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type='image/jpeg')


class DataSourceLogoImageView(View):

    def get(self, request, dataSourceId):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(pk=dataSourceId)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = ImageModel.objects.get(pk=datasource.logoId)
        except ImageModel.DoesNotExist:
            return JsonResponse({'error': 'Logo image not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the binary image data as the HTTP response
        return HttpResponse(image.image_data, content_type='image/jpeg')


class DataSourcesView(View):
    def get(self, request):
        dataSourceId_param = request.GET.get('dataSourceId')
        if dataSourceId_param:
            data_sources = DataSource.objects.filter(pk=dataSourceId_param)
        else:
            data_sources = DataSource.objects.all()
        data_sources, pagination_data = paginate_queryset(
            data_sources, request)
        serialized_data_sources = []
        for data_source in data_sources:
            try:
                data_disclosure_agreements = DataDisclosureAgreement.objects.filter(
                    dataSourceId=data_source, status='listed')
            except DataDisclosureAgreement.DoesNotExist:
                data_disclosure_agreements = None

            try:
                verification = Verification.objects.get(
                    dataSourceId=data_source)
                verification_serializer = VerificationSerializer(verification)
                verification_data = verification_serializer.data
            except Verification.DoesNotExist:
                verification_data = {
                    'id': '',
                    'dataSourceId': '',
                    'presentationExchangeId': '',
                    'presentationState': '',
                    'presentationRecord': {},
                }

            data_disclosure_agreement_serializer = DataDisclosureAgreementsSerializer(
                data_disclosure_agreements, many=True)

            datasource_serializer = DataSourceSerializer(data_source)

            api = [data_source.openApiUrl]
            serialized_data_source = {
                'dataDisclosureAgreements': data_disclosure_agreement_serializer.data,
                'api': api,
                'dataSource': datasource_serializer.data,
                'verification': verification_data
            }
            # Append the serialized data source to the list
            serialized_data_sources.append(serialized_data_source)

        # Create the response data dictionary
        response_data = {
            'dataSources': serialized_data_sources,
            'pagination': pagination_data
        }

        # Return the JSON response
        return JsonResponse(response_data)
