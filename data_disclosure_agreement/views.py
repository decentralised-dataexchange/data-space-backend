from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status, permissions
from config.models import DataSource
from .models import DataDisclosureAgreement
from .serializers import DataDisclosureAgreementSerializer,DataDisclosureAgreementsSerializer
from dataspace_backend.utils import paginate_queryset

# Create your views here.


class DataDisclosureAgreementView(APIView):
    serializer_class = DataDisclosureAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dataDisclosureAgreementId):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data_disclosure_agreement = DataDisclosureAgreement.objects.get(pk=dataDisclosureAgreementId,dataSourceId=datasource)
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse({'error': 'Data Disclosure Agreement not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data_disclosure_agreement, context={'request': request})
        response_data = {
            'dataDisclosureAgreement': serializer.data,
        }
        return JsonResponse(response_data)
    
    def delete(self, request, dataDisclosureAgreementId):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data_disclosure_agreement = DataDisclosureAgreement.objects.get(pk=dataDisclosureAgreementId,dataSourceId=datasource)
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse({'error': 'Data Disclosure Agreement not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the data disclosure agreement
        data_disclosure_agreement.delete()

        return JsonResponse({},status=status.HTTP_204_NO_CONTENT)
    
class DataDisclosureAgreementsView(APIView):
    serializer_class = DataDisclosureAgreementsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_param = request.query_params.get('status')  # Get the 'status' query parameter
        
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        if status_param:  # Check if 'status' parameter is present
            data_disclosure_agreements = DataDisclosureAgreement.objects.filter(dataSourceId=datasource, status=status_param)
        else:
            data_disclosure_agreements = DataDisclosureAgreement.objects.filter(dataSourceId=datasource)

        data_disclosure_agreements, pagination_data = paginate_queryset(data_disclosure_agreements, request)
        
        if not data_disclosure_agreements.exists():
            return JsonResponse({'error': 'No Data Disclosure Agreements found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data_disclosure_agreements, many=True)
        response_data = {
            'dataDisclosureAgreements': serializer.data,
            'pagination': pagination_data,
        }
        return JsonResponse(response_data)
    
class DataDisclosureAgreementUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, dataDisclosureAgreementId):

        to_be_updated_status = request.data.get('status')

        allowed_statuses = ['listed', 'unlisted']
        if to_be_updated_status not in allowed_statuses:
            return JsonResponse({'error': 'Updating status to this value is not allowed'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse({'error': 'Data source not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data_disclosure_agreement = DataDisclosureAgreement.objects.get(pk=dataDisclosureAgreementId,dataSourceId=datasource)
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse({'error': 'Data Disclosure Agreement not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        if data_disclosure_agreement.status not in ['approved', 'listed', 'unlisted']:
            return JsonResponse({'error': 'Data Disclosure Agreement status cannot be updated'}, status=status.HTTP_400_BAD_REQUEST)
        
        data_disclosure_agreement.status = to_be_updated_status
        data_disclosure_agreement.save()

        return JsonResponse({},status=status.HTTP_204_NO_CONTENT)
    
    