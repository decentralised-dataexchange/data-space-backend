from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status, permissions
from config.models import DataSource
from .models import DataDisclosureAgreement
from .serializers import (
    DataDisclosureAgreementSerializer,
    DataDisclosureAgreementsSerializer,
)
from dataspace_backend.utils import paginate_queryset
from django.db.models import Count

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
