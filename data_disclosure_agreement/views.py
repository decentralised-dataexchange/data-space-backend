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
                ddas_for_template_id = DataDisclosureAgreement.list_by_data_source_id(
                    templateId=dda_template_id,
                    data_source_id=datasource.id,
                    status=status_param,
                )
                revisions = []
                serializer = self.serializer_class(ddas_for_template_id, many=True)

                for index, dda in enumerate(serializer.data):
                    if index == 0:
                        temp_dda = dda["dataDisclosureAgreementRecord"]
                    else:
                        revisions.append(dda["dataDisclosureAgreementRecord"])
                if temp_dda:
                    temp_dda["revisions"] = revisions
                    ddas.append(temp_dda)
        else:
            temp_dda = {}
            for dda_template_id in data_disclosure_agreements_template_ids:
                ddas_for_template_id = DataDisclosureAgreement.list_by_data_source_id(
                    templateId=dda_template_id, data_source_id=datasource.id
                )
                revisions = []
                serializer = self.serializer_class(ddas_for_template_id, many=True)
                for dda in serializer.data:
                    if dda["isLatestVersion"]:
                        temp_dda = dda["dataDisclosureAgreementRecord"]
                    else:
                        revisions.append(dda["dataDisclosureAgreementRecord"])
                temp_dda["revisions"] = revisions
                ddas.append(temp_dda)

        ddas, pagination_data = paginate_queryset(ddas, request)

        response_data = {
            "dataDisclosureAgreements": ddas,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


class DataDisclosureAgreementUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, dataDisclosureAgreementId):

        to_be_updated_status = request.data.get("status")

        allowed_statuses = ["listed", "unlisted", "awaitingForApproval"]
        if to_be_updated_status not in allowed_statuses:
            return JsonResponse(
                {"error": "Updating status to this value is not allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        if data_disclosure_agreement.status not in ["approved", "listed", "unlisted"]:
            return JsonResponse(
                {"error": "Data Disclosure Agreement status cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dda_record = data_disclosure_agreement.dataDisclosureAgreementRecord
        dda_record["status"] = to_be_updated_status
        data_disclosure_agreement.status = to_be_updated_status
        data_disclosure_agreement.dataDisclosureAgreementRecord = dda_record
        data_disclosure_agreement.save()

        return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
