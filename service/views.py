import uuid
import requests
import json
from django.shortcuts import render
from django.db.models import Q
from rest_framework.views import View
from config.models import DataSource, ImageModel, Verification
from config.serializers import VerificationSerializer, DataSourceSerializer
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from data_disclosure_agreement.models import (
    DataDisclosureAgreement,
    DataDisclosureAgreementTemplate,
)
from data_disclosure_agreement.serializers import (
    DataDisclosureAgreementsSerializer,
    DataDisclosureAgreementTemplatesSerializer,
)
from dataspace_backend.utils import paginate_queryset
from organisation.models import Organisation, OrganisationIdentity
from organisation.serializers import (
    OrganisationIdentitySerializer,
    OrganisationSerializer,
)
from oAuth2Clients.models import OrganisationOAuth2Clients
from software_statement.models import SoftwareStatement


# Create your views here.


class DataSourceCoverImageView(View):

    def get(self, request, dataSourceId):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(pk=dataSourceId)
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


class DataSourceLogoImageView(View):

    def get(self, request, dataSourceId):
        try:
            # Get the DataSource instance
            datasource = DataSource.objects.get(pk=dataSourceId)
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


class DataSourcesView(View):
    def get(self, request):
        dataSourceId_param = request.GET.get("dataSourceId")

        if dataSourceId_param:
            data_sources = DataSource.objects.filter(pk=dataSourceId_param)
        else:
            data_sources = DataSource.objects.all().order_by("createdAt")

        data_sources, pagination_data = paginate_queryset(data_sources, request)
        serialized_data_sources = []
        for data_source in data_sources:

            data_disclosure_agreements_template_ids = (
                DataDisclosureAgreement.list_unique_dda_template_ids_for_a_data_source(
                    data_source_id=data_source.id
                )
            )
            ddas = []
            for dda_template_id in data_disclosure_agreements_template_ids:
                dda_for_template_id = DataDisclosureAgreement.read_latest_dda_by_template_id_and_data_source_id(
                    template_id=dda_template_id,
                    data_source_id=data_source.id,
                )

                data_disclosure_agreement_serializer = (
                    DataDisclosureAgreementsSerializer(dda_for_template_id)
                )
                dda = data_disclosure_agreement_serializer.data[
                    "dataDisclosureAgreementRecord"
                ]

                if dda:
                    dda["status"] = data_disclosure_agreement_serializer.data["status"]
                    dda["isLatestVersion"] = data_disclosure_agreement_serializer.data[
                        "isLatestVersion"
                    ]
                    ddas.append(dda)

            try:
                verification = Verification.objects.get(dataSourceId=data_source)
                verification_serializer = VerificationSerializer(verification)
                verification_data = verification_serializer.data
            except Verification.DoesNotExist:
                verification_data = {
                    "id": "",
                    "dataSourceId": "",
                    "presentationExchangeId": "",
                    "presentationState": "",
                    "presentationRecord": {},
                }

            datasource_serializer = DataSourceSerializer(data_source)

            api = [data_source.openApiUrl]
            serialized_data_source = {
                "dataDisclosureAgreements": ddas,
                "api": api,
                "dataSource": datasource_serializer.data,
                "verification": verification_data,
            }
            # Append the serialized data source to the list
            serialized_data_sources.append(serialized_data_source)

        # Create the response data dictionary
        response_data = {
            "dataSources": serialized_data_sources,
            "pagination": pagination_data,
        }

        # Return the JSON response
        return JsonResponse(response_data)


class OrganisationCoverImageView(View):

    def get(self, request, organisationId):
        try:
            # Get the organisation instance
            organisation = Organisation.objects.get(pk=organisationId)
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


class OrganisationLogoImageView(View):

    def get(self, request, organisationId):
        try:
            # Get the organisation instance
            organisation = Organisation.objects.get(pk=organisationId)
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


class OrganisationsView(View):
    def get(self, request):
        organisation_id_param = request.GET.get("organisationId")

        if organisation_id_param:
            try:
                organisation_uuid = uuid.UUID(organisation_id_param)
                organisations = Organisation.objects.filter(pk=organisation_uuid)
            except ValueError:
                return JsonResponse({"error": "Invalid organisationId"}, status=400)
            organisations = Organisation.objects.filter(pk=organisation_id_param)
        else:
            organisations = Organisation.objects.all().order_by("createdAt")

        organisations, pagination_data = paginate_queryset(organisations, request)
        serialized_organisations = []
        for organisation in organisations:

            data_disclosure_agreements_template_ids = DataDisclosureAgreementTemplate.list_unique_dda_template_ids_for_a_data_source(
                data_source_id=organisation.id
            )
            ddas = []
            for dda_template_id in data_disclosure_agreements_template_ids:
                dda_for_template_id = DataDisclosureAgreementTemplate.read_latest_dda_by_template_id_and_data_source_id(
                    template_id=dda_template_id,
                    data_source_id=organisation.id,
                )

                data_disclosure_agreement_serializer = (
                    DataDisclosureAgreementTemplatesSerializer(dda_for_template_id)
                )
                dda = data_disclosure_agreement_serializer.data[
                    "dataDisclosureAgreementRecord"
                ]

                if dda:
                    dda["status"] = data_disclosure_agreement_serializer.data["status"]
                    dda["isLatestVersion"] = data_disclosure_agreement_serializer.data[
                        "isLatestVersion"
                    ]
                    dda["createdAt"] = data_disclosure_agreement_serializer.data["createdAt"]
                    dda["updatedAt"] = data_disclosure_agreement_serializer.data["updatedAt"]
                    ddas.append(dda)

            try:
                verification = OrganisationIdentity.objects.get(
                    organisationId=organisation
                )
                verification_serializer = OrganisationIdentitySerializer(verification)
                verification_data = verification_serializer.data
            except OrganisationIdentity.DoesNotExist:
                verification_data = {
                    "id": "",
                    "organisationId": "",
                    "presentationExchangeId": "",
                    "presentationState": "",
                    "isPresentationVerified": False,
                    "presentationRecord": {},
                }

            try:
                software_statement = SoftwareStatement.objects.get(organisationId=organisation)
                software_statement = software_statement.credentialHistory
            except SoftwareStatement.DoesNotExist:
                software_statement = {}

            organisation_serializer = OrganisationSerializer(organisation)
            organisation_data = organisation_serializer.data
            organisation_data["softwareStatement"] = software_statement

            api = [organisation.openApiUrl]
            serialized_organisation = {
                "dataDisclosureAgreements": ddas,
                "api": api,
                "organisation": organisation_data,
                "organisationIdentity": verification_data,
            }
            # Append the serialized organisation to the list
            serialized_organisations.append(serialized_organisation)

        # Create the response data dictionary
        response_data = {
            "organisations": serialized_organisations,
            "pagination": pagination_data,
        }

        # Return the JSON response
        return JsonResponse(response_data)


class SearchView(View):
    def get(self, request):
        search = request.GET.get("search", "")
        if not search or not search.strip():
            return JsonResponse(
                {
                    "error": "invalid_request",
                    "error_description": "search parameter is required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_search_org_name = request.GET.get("searchOrgName")
        raw_search_dda_purpose = request.GET.get("searchDdaPurpose")
        raw_search_dda_description = request.GET.get("searchDdaDescription")
        raw_search_dataset = request.GET.get("searchDataset")

        def parse_bool_param(raw_value, param_name, default=True):
            if raw_value is None:
                return default
            value = str(raw_value).lower()
            if value == "true":
                return True
            if value == "false":
                return False
            raise ValueError(
                f"Invalid value for {param_name}; expected 'true' or 'false'"
            )

        try:
            search_org_name = parse_bool_param(
                raw_search_org_name, "searchOrgName", True
            )
            search_dda_purpose = parse_bool_param(
                raw_search_dda_purpose, "searchDdaPurpose", True
            )
            search_dda_description = parse_bool_param(
                raw_search_dda_description, "searchDdaDescription", True
            )
            search_dataset = parse_bool_param(
                raw_search_dataset, "searchDataset", True
            )
        except ValueError as exc:
            return JsonResponse(
                {
                    "error": "invalid_request",
                    "error_description": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not any(
            [search_org_name, search_dda_purpose, search_dda_description, search_dataset]
        ):
            return JsonResponse(
                {
                    "error": "invalid_request",
                    "error_description": "At least one search scope must be true",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        sort_by = request.GET.get("sortBy", "relevance")
        sort_order = request.GET.get("sortOrder", "desc")

        allowed_sort_by = {"relevance", "orgName", "orgCreatedAt", "ddaCreatedAt"}
        if sort_by not in allowed_sort_by:
            return JsonResponse(
                {
                    "error": "invalid_request",
                    "error_description": "Invalid sortBy parameter",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_sort_order = {"asc", "desc"}
        if sort_order not in allowed_sort_order:
            return JsonResponse(
                {
                    "error": "invalid_request",
                    "error_description": "Invalid sortOrder parameter",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        dda_scopes_enabled = (
            search_dda_purpose or search_dda_description or search_dataset
        )

        ddas_qs = DataDisclosureAgreementTemplate.objects.none()
        organisation_ids_from_ddas = []
        if dda_scopes_enabled:
            # Start from all listed, latest DDAs
            base_ddas_qs = DataDisclosureAgreementTemplate.objects.filter(
                status="listed",
                isLatestVersion=True,
            ).select_related("organisationId")

            # Scan JSON records in Python to find matches
            search_lower = search.lower()
            matching_ids = []
            org_ids_set = set()
            for dda in base_ddas_qs:
                record = dda.dataDisclosureAgreementRecord or {}
                record_str = json.dumps(record).lower()
                if search_lower in record_str:
                    matching_ids.append(dda.id)
                    org_ids_set.add(dda.organisationId_id)

            if matching_ids:
                ddas_qs = base_ddas_qs.filter(id__in=matching_ids)
                organisation_ids_from_ddas = list(org_ids_set)

        org_filter = Q()
        has_filter = False

        if search_org_name:
            org_filter |= Q(name__icontains=search) | Q(description__icontains=search)
            has_filter = True

        if dda_scopes_enabled and organisation_ids_from_ddas:
            org_filter |= Q(id__in=organisation_ids_from_ddas)
            has_filter = True

        if has_filter:
            organisations_qs = Organisation.objects.filter(org_filter).distinct()
        else:
            organisations_qs = Organisation.objects.none()

        if sort_by == "orgName":
            order_field = "name" if sort_order == "asc" else "-name"
            organisations_qs = organisations_qs.order_by(order_field)
        else:
            order_field = "createdAt" if sort_order == "asc" else "-createdAt"
            organisations_qs = organisations_qs.order_by(order_field)

        if dda_scopes_enabled:
            if sort_by == "ddaCreatedAt":
                dda_order_field = "createdAt" if sort_order == "asc" else "-createdAt"
            elif sort_by == "orgName":
                dda_order_field = (
                    "organisationId__name"
                    if sort_order == "asc"
                    else "-organisationId__name"
                )
            else:
                dda_order_field = "-createdAt" if sort_order == "desc" else "createdAt"
            ddas_qs = ddas_qs.order_by(dda_order_field)

        organisations_page, organisations_pagination = paginate_queryset(
            organisations_qs, request
        )

        serialized_organisations = []
        for organisation in organisations_page:
            data_disclosure_agreements_template_ids = DataDisclosureAgreementTemplate.list_unique_dda_template_ids_for_a_data_source(
                data_source_id=organisation.id
            )
            ddas = []
            for dda_template_id in data_disclosure_agreements_template_ids:
                dda_for_template_id = DataDisclosureAgreementTemplate.read_latest_dda_by_template_id_and_data_source_id(
                    template_id=dda_template_id,
                    data_source_id=organisation.id,
                )

                data_disclosure_agreement_serializer = (
                    DataDisclosureAgreementTemplatesSerializer(dda_for_template_id)
                )
                dda = data_disclosure_agreement_serializer.data[
                    "dataDisclosureAgreementRecord"
                ]

                if dda:
                    dda["status"] = data_disclosure_agreement_serializer.data["status"]
                    dda["isLatestVersion"] = data_disclosure_agreement_serializer.data[
                        "isLatestVersion"
                    ]
                    dda["createdAt"] = data_disclosure_agreement_serializer.data[
                        "createdAt"
                    ]
                    dda["updatedAt"] = data_disclosure_agreement_serializer.data[
                        "updatedAt"
                    ]
                    ddas.append(dda)

            try:
                verification = OrganisationIdentity.objects.get(organisationId=organisation)
                verification_serializer = OrganisationIdentitySerializer(verification)
                verification_data = verification_serializer.data
            except OrganisationIdentity.DoesNotExist:
                verification_data = {
                    "id": "",
                    "organisationId": "",
                    "presentationExchangeId": "",
                    "presentationState": "",
                    "isPresentationVerified": False,
                    "presentationRecord": {},
                }

            try:
                software_statement = SoftwareStatement.objects.get(
                    organisationId=organisation
                )
                software_statement = software_statement.credentialHistory
            except SoftwareStatement.DoesNotExist:
                software_statement = {}

            organisation_serializer = OrganisationSerializer(organisation)
            organisation_data = organisation_serializer.data
            organisation_data["softwareStatement"] = software_statement

            api = [organisation.openApiUrl]
            serialized_organisation = {
                "dataDisclosureAgreements": ddas,
                "api": api,
                "organisation": organisation_data,
                "organisationIdentity": verification_data,
            }
            serialized_organisations.append(serialized_organisation)

        ddas_page, ddas_pagination = paginate_queryset(ddas_qs, request)

        serialized_ddas = []
        for dda in ddas_page:
            dda_serializer = DataDisclosureAgreementTemplatesSerializer(dda)
            dda_data = dda_serializer.data
            serialized_ddas.append(
                {
                    "id": dda_data["id"],
                    "organisationId": dda_data["organisationId"],
                    "organisationName": dda.organisationId.name,
                    "dataDisclosureAgreementRecord": dda_data[
                        "dataDisclosureAgreementRecord"
                    ],
                    "status": dda_data["status"],
                    "isLatestVersion": dda_data["isLatestVersion"],
                    "createdAt": dda_data["createdAt"],
                    "updatedAt": dda_data["updatedAt"],
                }
            )

        response_data = {
            "organisations": serialized_organisations,
            "organisationsPagination": organisations_pagination,
            "ddas": serialized_ddas,
            "ddasPagination": ddas_pagination,
            "searchMeta": {
                "query": search,
                "searchOrgName": search_org_name,
                "searchDdaPurpose": search_dda_purpose,
                "searchDdaDescription": search_dda_description,
                "searchDataset": search_dataset,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            },
        }

        return JsonResponse(response_data)
