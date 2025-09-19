from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status, permissions
from config.models import DataSource
from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate
from .serializers import (
    DataDisclosureAgreementSerializer,
    DataDisclosureAgreementsSerializer,
    DataDisclosureAgreementTemplateSerializer,
    DataDisclosureAgreementTemplatesSerializer
)
from dataspace_backend.utils import paginate_queryset
from django.db.models import Count
from organisation.models import Organisation
from data_disclosure_agreement_record.serializers import DataDisclosureAgreementRecordHistorySerializer
from data_disclosure_agreement_record.models import DataDisclosureAgreementRecordHistory

# Create your views here.


class DataDisclosureAgreementView(APIView):
    serializer_class = DataDisclosureAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dataDisclosureAgreementId):
        version_param = request.query_params.get("version")
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if version_param:
                data_disclosure_agreement = DataDisclosureAgreement.objects.get(
                    templateId=dataDisclosureAgreementId,
                    dataSourceId=datasource,
                    version=version_param,
                )
            else:
                data_disclosure_agreement = DataDisclosureAgreement.objects.filter(
                    templateId=dataDisclosureAgreementId, dataSourceId=datasource
                ).last()
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(
            data_disclosure_agreement, context={"request": request}
        )
        dda = serializer.data["dataDisclosureAgreementRecord"]
        dda['status'] = serializer.data['status']
        dda['isLatestVersion'] = serializer.data['isLatestVersion']
        response_data = {
            "dataDisclosureAgreement": dda,
        }

        return JsonResponse(response_data)

    def delete(self, request, dataDisclosureAgreementId):
        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data_disclosure_agreement_revisions = (
                DataDisclosureAgreement.objects.filter(
                    templateId=dataDisclosureAgreementId, dataSourceId=datasource
                )
            )
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete the data disclosure agreement
        data_disclosure_agreement_revisions.delete()

        return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)


class DataDisclosureAgreementsView(APIView):
    serializer_class = DataDisclosureAgreementsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the 'status' query parameter
        status_param = request.query_params.get("status")

        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        data_disclosure_agreements_template_ids = (
            DataDisclosureAgreement.list_unique_dda_template_ids_for_a_data_source(
                data_source_id=datasource.id
            )
        )

        ddas = []

        if status_param:
            temp_dda = {}
            for dda_template_id in data_disclosure_agreements_template_ids:
                latest_dda_for_template_id = (
                    DataDisclosureAgreement.objects.filter(
                        templateId=dda_template_id,
                        dataSourceId=datasource,
                        status=status_param,
                    )
                    .order_by("-createdAt")
                    .first()
                )
                
                serializer = self.serializer_class(latest_dda_for_template_id)
                temp_dda = serializer.data["dataDisclosureAgreementRecord"]

                if temp_dda:
                    temp_dda['status'] = serializer.data['status']
                    temp_dda['isLatestVersion'] = serializer.data['isLatestVersion']
                    ddas.append(temp_dda)
        else:
            temp_dda = {}
            for dda_template_id in data_disclosure_agreements_template_ids:
                latest_dda_for_template_id = (
                    DataDisclosureAgreement.objects.filter(
                        templateId=dda_template_id,
                        dataSourceId=datasource,
                        isLatestVersion=True,
                    )
                    .order_by("-createdAt")
                    .first()
                )
                serializer = self.serializer_class(latest_dda_for_template_id)
                temp_dda = serializer.data["dataDisclosureAgreementRecord"]
                if temp_dda:
                    temp_dda['status'] = serializer.data['status']
                    temp_dda['isLatestVersion'] = serializer.data['isLatestVersion']
                    ddas.append(temp_dda)

        ddas, pagination_data = paginate_queryset(ddas, request)

        response_data = {
            "dataDisclosureAgreements": ddas,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


def validate_update_dda_request_body(to_be_updated_status: str, current_status: str):
    if current_status == "unlisted" and to_be_updated_status == "awaitingForApproval":
        return True
    elif current_status == "approved" and to_be_updated_status == "listed":
        return True
    elif current_status == "rejected" and to_be_updated_status == "awaitingForApproval":
        return True
    elif current_status == "listed" and to_be_updated_status == "unlisted":
        return True
    else:
        return False


class DataDisclosureAgreementUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, dataDisclosureAgreementId):

        to_be_updated_status = request.data.get("status")

        try:
            datasource = DataSource.objects.get(admin=request.user)
        except DataSource.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data_disclosure_agreement = DataDisclosureAgreement.objects.get(
                templateId=dataDisclosureAgreementId,
                dataSourceId=datasource,
                isLatestVersion=True,
            )
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        is_valid_dda_status = validate_update_dda_request_body(
            to_be_updated_status=to_be_updated_status,
            current_status=data_disclosure_agreement.status,
        )

        if is_valid_dda_status:
            dda_record = data_disclosure_agreement.dataDisclosureAgreementRecord
            dda_record["status"] = to_be_updated_status
            data_disclosure_agreement.status = to_be_updated_status
            data_disclosure_agreement.dataDisclosureAgreementRecord = dda_record
            data_disclosure_agreement.save()
            
            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse(
                {"error": "Data Disclosure Agreement status cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        

class DataDisclosureAgreementTempleteView(APIView):
    serializer_class = DataDisclosureAgreementTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dataDisclosureAgreementId):
        version_param = request.query_params.get("version")
        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if version_param:
                data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                    status='archived'
                ).get(
                    templateId=dataDisclosureAgreementId,
                    organisationId=organisation,
                    version=version_param,
                )
            else:
                data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                    status='archived'
                ).filter(
                    templateId=dataDisclosureAgreementId, 
                    organisationId=organisation,
                ).last()
                
                if not data_disclosure_agreement:
                    return JsonResponse(
                        {"error": "Active Data Disclosure Agreement not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                    
        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(
            data_disclosure_agreement, context={"request": request}
        )
        dda = serializer.data["dataDisclosureAgreementRecord"]
        dda['status'] = serializer.data['status']
        dda['isLatestVersion'] = serializer.data['isLatestVersion']
        response_data = {
            "dataDisclosureAgreement": dda,
        }

        return JsonResponse(response_data)


class DataDisclosureAgreementTemplatesView(APIView):
    serializer_class = DataDisclosureAgreementTemplatesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get the 'status' query parameter
        status_param = request.query_params.get("status")

        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        data_disclosure_agreements_template_ids = (
            DataDisclosureAgreementTemplate.list_unique_dda_template_ids_for_a_data_source(
                data_source_id=organisation.id
            )
        )

        ddas = []

        if status_param:
            for dda_template_id in data_disclosure_agreements_template_ids:
                # Get all non-archived DDAs for this template ID with the specified status
                ddas_for_template = list(DataDisclosureAgreementTemplate.objects.exclude(
                    status='archived'
                ).filter(
                    templateId=dda_template_id,
                    organisationId=organisation,
                    status=status_param,
                ))
                
                if not ddas_for_template:
                    continue
                    
                # Find the latest version using isLatestVersion field
                latest_dda = next((dda for dda in ddas_for_template if dda.isLatestVersion), None)
                if not latest_dda:
                    continue  # Skip if no latest version is marked
                
                # Serialize the latest DDA
                latest_serializer = self.serializer_class(latest_dda)
                latest_dda_data = latest_serializer.data["dataDisclosureAgreementRecord"]
                latest_dda_data['status'] = latest_serializer.data['status']
                latest_dda_data['isLatestVersion'] = True
                
                # Serialize all other versions as revisions
                revisions = []
                for dda in ddas_for_template:
                    if dda.id != latest_dda.id:  # Skip the latest DDA
                        serializer = self.serializer_class(dda)
                        revision_data = serializer.data["dataDisclosureAgreementRecord"]
                        revision_data['status'] = serializer.data['status']
                        revision_data['isLatestVersion'] = False
                        revision_data['version'] = dda.version
                        revision_data['createdAt'] = dda.createdAt.isoformat()
                        revisions.append(revision_data)
                
                # Add revisions to the latest DDA, sorted by createdAt
                latest_dda_data['revisions'] = sorted(revisions, key=lambda x: x['createdAt'], reverse=True)
                ddas.append(latest_dda_data)
        else:
            for dda_template_id in data_disclosure_agreements_template_ids:
                # Get all non-archived DDAs for this template ID
                ddas_for_template = list(DataDisclosureAgreementTemplate.objects.exclude(
                    status='archived'
                ).filter(
                    templateId=dda_template_id,
                    organisationId=organisation,
                ))
                
                if not ddas_for_template:
                    continue
                    
                # Find the latest version using isLatestVersion field
                latest_dda = next((dda for dda in ddas_for_template if dda.isLatestVersion), None)
                if not latest_dda:
                    continue  # Skip if no latest version is marked
                
                # Serialize the latest DDA
                latest_serializer = self.serializer_class(latest_dda)
                latest_dda_data = latest_serializer.data["dataDisclosureAgreementRecord"]
                latest_dda_data['status'] = latest_serializer.data['status']
                latest_dda_data['isLatestVersion'] = True
                
                # Serialize all other versions as revisions
                revisions = []
                for dda in ddas_for_template:
                    if dda.id != latest_dda.id:  # Skip the latest DDA
                        serializer = self.serializer_class(dda)
                        revision_data = serializer.data["dataDisclosureAgreementRecord"]
                        revision_data['status'] = serializer.data['status']
                        revision_data['isLatestVersion'] = False
                        revision_data['version'] = dda.version
                        revision_data['createdAt'] = dda.createdAt.isoformat()
                        revisions.append(revision_data)
                
                # Add revisions to the latest DDA, sorted by createdAt
                latest_dda_data['revisions'] = sorted(revisions, key=lambda x: x['createdAt'], reverse=True)
                ddas.append(latest_dda_data)

        ddas, pagination_data = paginate_queryset(ddas, request)

        response_data = {
            "dataDisclosureAgreements": ddas,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)
    
class DataDisclosureAgreementTemplateUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, dataDisclosureAgreementId):

        to_be_updated_status = request.data.get("status")

        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                status='archived'
            ).get(
                templateId=dataDisclosureAgreementId,
                organisationId=organisation,
                isLatestVersion=True,
            )
        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        is_valid_dda_status = validate_update_dda_request_body(
            to_be_updated_status=to_be_updated_status,
            current_status=data_disclosure_agreement.status,
        )

        if is_valid_dda_status:
            dda_record = data_disclosure_agreement.dataDisclosureAgreementRecord
            dda_record["status"] = to_be_updated_status
            data_disclosure_agreement.status = to_be_updated_status
            data_disclosure_agreement.dataDisclosureAgreementRecord = dda_record
            data_disclosure_agreement.save()
            
            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse(
                {"error": "Data Disclosure Agreement status cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
class DataDisclosureAgreementHistoryView(APIView):
    serializer_class = DataDisclosureAgreementRecordHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dataDisclosureAgreementId):
        dda_template_id = dataDisclosureAgreementId

        try:
            organisation = Organisation.objects.get(admin=request.user)
        except Organisation.DoesNotExist:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        ddas_for_template = list(DataDisclosureAgreementTemplate.objects.exclude(
            status='archived'
        ).filter(
            templateId=dda_template_id,
            organisationId=organisation,
        ))

        
        try:
            dda_records = DataDisclosureAgreementRecordHistory.objects.filter(organisationId=organisation,dataDisclosureAgreementTemplateId=dda_template_id).order_by("-createdAt")
        except DataDisclosureAgreementRecordHistory.DoesNotExist:
            dda_records = None

        serializer = self.serializer_class(dda_records, many=True)

        dda_records, pagination_data = paginate_queryset(serializer.data, request)

        response_data = {
            "dataDisclosureAgreementRecordHistory": dda_records,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)