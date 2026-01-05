from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.views import APIView

from data_disclosure_agreement_record.models import DataDisclosureAgreementRecordHistory
from data_disclosure_agreement_record.serializers import (
    DataDisclosureAgreementRecordHistorySerializer,
)
from dataspace_backend.utils import (
    get_datasource_or_400,
    get_organisation_or_400,
    paginate_queryset,
)

from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate
from .serializers import (
    DataDisclosureAgreementSerializer,
    DataDisclosureAgreementsSerializer,
    DataDisclosureAgreementTemplateSerializer,
    DataDisclosureAgreementTemplatesSerializer,
)


class DataDisclosureAgreementView(APIView):
    serializer_class = DataDisclosureAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dataDisclosureAgreementId):
        version_param = request.query_params.get("version")
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

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
        dda["status"] = serializer.data["status"]
        dda["isLatestVersion"] = serializer.data["isLatestVersion"]
        response_data = {
            "dataDisclosureAgreement": dda,
        }

        return JsonResponse(response_data)

    def delete(self, request, dataDisclosureAgreementId):
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

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

        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        data_disclosure_agreements_template_ids = (
            DataDisclosureAgreement.list_unique_dda_template_ids_for_a_data_source(
                data_source_id=datasource.id
            )
        )

        ddas = []

        temp_dda = {}
        for dda_template_id in data_disclosure_agreements_template_ids:
            filter_kwargs = {"templateId": dda_template_id, "dataSourceId": datasource}
            if status_param:
                filter_kwargs["status"] = status_param
            else:
                filter_kwargs["isLatestVersion"] = True

            latest_dda_for_template_id = (
                DataDisclosureAgreement.objects.filter(**filter_kwargs)
                .order_by("-createdAt")
                .first()
            )

            serializer = self.serializer_class(latest_dda_for_template_id)
            temp_dda = serializer.data["dataDisclosureAgreementRecord"]

            if temp_dda:
                temp_dda["status"] = serializer.data["status"]
                temp_dda["isLatestVersion"] = serializer.data["isLatestVersion"]
                ddas.append(temp_dda)

        ddas, pagination_data = paginate_queryset(ddas, request)

        response_data = {
            "dataDisclosureAgreements": ddas,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


ALLOWED_DDA_STATUS_TRANSITIONS = {
    ("unlisted", "awaitingForApproval"),
    ("approved", "listed"),
    ("rejected", "awaitingForApproval"),
    ("listed", "unlisted"),
}


def validate_update_dda_request_body(to_be_updated_status: str, current_status: str):
    return (current_status, to_be_updated_status) in ALLOWED_DDA_STATUS_TRANSITIONS


class DataDisclosureAgreementUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, dataDisclosureAgreementId):
        to_be_updated_status = request.data.get("status")

        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

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
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            if version_param:
                data_disclosure_agreement = (
                    DataDisclosureAgreementTemplate.objects.exclude(
                        status="archived"
                    ).get(
                        templateId=dataDisclosureAgreementId,
                        organisationId=organisation,
                        version=version_param,
                    )
                )
            else:
                data_disclosure_agreement = (
                    DataDisclosureAgreementTemplate.objects.exclude(status="archived")
                    .filter(
                        templateId=dataDisclosureAgreementId,
                        organisationId=organisation,
                    )
                    .last()
                )

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
        dda["status"] = serializer.data["status"]
        dda["isLatestVersion"] = serializer.data["isLatestVersion"]
        dda["createdAt"] = serializer.data["createdAt"]
        dda["updatedAt"] = serializer.data["updatedAt"]
        response_data = {
            "dataDisclosureAgreement": dda,
        }

        return JsonResponse(response_data)


class DataDisclosureAgreementTemplatesView(APIView):
    serializer_class = DataDisclosureAgreementTemplatesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _build_latest_dda_payload(self, ddas_for_template):
        if not ddas_for_template:
            return None

        latest_dda = next(
            (dda for dda in ddas_for_template if dda.isLatestVersion), None
        )
        if not latest_dda:
            return None

        latest_serializer = self.serializer_class(latest_dda)
        latest_dda_data = latest_serializer.data["dataDisclosureAgreementRecord"]
        latest_dda_data["status"] = latest_serializer.data["status"]
        latest_dda_data["isLatestVersion"] = True
        latest_dda_data["createdAt"] = latest_serializer.data["createdAt"]
        latest_dda_data["updatedAt"] = latest_serializer.data["updatedAt"]

        revisions = []
        for dda in ddas_for_template:
            if dda.id != latest_dda.id:  # Skip the latest DDA
                serializer = self.serializer_class(dda)
                revision_data = serializer.data["dataDisclosureAgreementRecord"]
                revision_data["status"] = serializer.data["status"]
                revision_data["isLatestVersion"] = False
                revision_data["version"] = dda.version
                revision_data["createdAt"] = dda.createdAt
                revision_data["updatedAt"] = dda.updatedAt
                revisions.append(revision_data)

        latest_dda_data["revisions"] = sorted(
            revisions, key=lambda x: x["createdAt"], reverse=True
        )
        return latest_dda_data

    def get(self, request):
        # Get the 'status' query parameter
        status_param = request.query_params.get("status")

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        data_disclosure_agreements_template_ids = DataDisclosureAgreementTemplate.list_unique_dda_template_ids_for_a_data_source(
            data_source_id=organisation.id
        )

        ddas = []

        for dda_template_id in data_disclosure_agreements_template_ids:
            filter_kwargs = {
                "templateId": dda_template_id,
                "organisationId": organisation,
            }
            if status_param:
                filter_kwargs["status"] = status_param

            # Get all non-archived DDAs for this template ID
            ddas_for_template = list(
                DataDisclosureAgreementTemplate.objects.exclude(
                    status="archived"
                ).filter(**filter_kwargs)
            )

            latest_dda_data = self._build_latest_dda_payload(ddas_for_template)
            if not latest_dda_data:
                continue
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
        dda_template_id = dataDisclosureAgreementId

        to_be_updated_status = request.data.get("status")

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                status="archived"
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
            if to_be_updated_status == "listed":
                # Iterate through existing DDAs and mark `isLatestVersion=false`
                existing_ddas = DataDisclosureAgreementTemplate.objects.filter(
                    templateId=dda_template_id,
                    organisationId=organisation,
                    isLatestVersion=False,
                )
                for existing_dda in existing_ddas:
                    if existing_dda.status != "archived":
                        existing_dda.status = "unlisted"
                    existing_dda.save()
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


class DataDisclosureAgreementHistoriesView(APIView):
    serializer_class = DataDisclosureAgreementRecordHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dataDisclosureAgreementId):
        dda_template_id = dataDisclosureAgreementId

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            dda_records = DataDisclosureAgreementRecordHistory.objects.filter(
                organisationId=organisation,
                dataDisclosureAgreementTemplateId=dda_template_id,
            ).order_by("-updatedAt")
        except DataDisclosureAgreementRecordHistory.DoesNotExist:
            dda_records = None

        serializer = self.serializer_class(dda_records, many=True)

        dda_records, pagination_data = paginate_queryset(serializer.data, request)

        response_data = {
            "dataDisclosureAgreementRecordHistory": dda_records,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


class DataDisclosureAgreementHistoryView(APIView):
    serializer_class = DataDisclosureAgreementRecordHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, dataDisclosureAgreementId, pk):
        """Delete a specific history record by its primary key"""
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            record = DataDisclosureAgreementRecordHistory.objects.get(
                pk=pk,
                organisationId=organisation,
                dataDisclosureAgreementTemplateId=dataDisclosureAgreementId,
            )
            record.delete()
            return JsonResponse(
                {
                    "message": "Data disclosure agreement history record deleted successfully"
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        except DataDisclosureAgreementRecordHistory.DoesNotExist:
            return JsonResponse(
                {
                    "error": "Data disclosure agreement history record not found or access denied"
                },
                status=status.HTTP_404_NOT_FOUND,
            )
