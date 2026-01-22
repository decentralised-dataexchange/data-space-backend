import json
import uuid
from typing import Any, cast

from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from rest_framework import status

from config.models import DataSource, Verification
from config.serializers import DataSourceSerializer, VerificationSerializer
from data_disclosure_agreement.models import (
    DataDisclosureAgreement,
    DataDisclosureAgreementTemplate,
)
from data_disclosure_agreement.serializers import (
    DataDisclosureAgreementsSerializer,
    DataDisclosureAgreementTemplatesSerializer,
)
from dataspace_backend.image_utils import get_image_response
from dataspace_backend.utils import get_instance_or_400, paginate_queryset
from organisation.models import Organisation, OrganisationIdentity
from organisation.serializers import (
    OrganisationIdentitySerializer,
    OrganisationSerializer,
)
from software_statement.models import SoftwareStatement


def _build_datasource_ddas(data_source: DataSource) -> list[dict[str, Any]]:
    data_disclosure_agreements_template_ids = (
        DataDisclosureAgreement.list_unique_dda_template_ids_for_a_data_source(
            data_source_id=str(data_source.id)
        )
    )
    ddas = []
    for dda_template_id in data_disclosure_agreements_template_ids:
        dda_for_template_id = (
            DataDisclosureAgreement.read_latest_dda_by_template_id_and_data_source_id(
                template_id=dda_template_id,
                data_source_id=str(data_source.id),
            )
        )

        data_disclosure_agreement_serializer = DataDisclosureAgreementsSerializer(
            dda_for_template_id
        )
        dda = data_disclosure_agreement_serializer.data["dataDisclosureAgreementRecord"]

        if dda:
            dda["status"] = data_disclosure_agreement_serializer.data["status"]
            dda["isLatestVersion"] = data_disclosure_agreement_serializer.data[
                "isLatestVersion"
            ]
            ddas.append(dda)
    return ddas


def _build_organisation_ddas(organisation: Organisation) -> list[dict[str, Any]]:
    data_disclosure_agreements_template_ids = (
        DataDisclosureAgreementTemplate.list_unique_dda_template_ids_for_a_data_source(
            data_source_id=str(organisation.id)
        )
    )
    ddas = []
    for dda_template_id in data_disclosure_agreements_template_ids:
        dda_for_template_id = DataDisclosureAgreementTemplate.read_latest_dda_by_template_id_and_data_source_id(
            template_id=dda_template_id,
            data_source_id=str(organisation.id),
        )

        data_disclosure_agreement_serializer = (
            DataDisclosureAgreementTemplatesSerializer(dda_for_template_id)
        )
        dda = data_disclosure_agreement_serializer.data["dataDisclosureAgreementRecord"]

        if dda:
            dda["status"] = data_disclosure_agreement_serializer.data["status"]
            dda["isLatestVersion"] = data_disclosure_agreement_serializer.data[
                "isLatestVersion"
            ]
            dda["createdAt"] = data_disclosure_agreement_serializer.data["createdAt"]
            dda["updatedAt"] = data_disclosure_agreement_serializer.data["updatedAt"]
            dda["tags"] = data_disclosure_agreement_serializer.data.get("tags", [])
            ddas.append(dda)
    return ddas


def _get_datasource_verification_payload(data_source: DataSource) -> dict[str, Any]:
    try:
        verification = Verification.objects.get(dataSourceId=data_source)
        verification_serializer = VerificationSerializer(verification)
        return verification_serializer.data
    except Verification.DoesNotExist:
        return {
            "id": "",
            "dataSourceId": "",
            "presentationExchangeId": "",
            "presentationState": "",
            "presentationRecord": {},
        }


def _get_organisation_identity_payload(organisation: Organisation) -> dict[str, Any]:
    try:
        verification = OrganisationIdentity.objects.get(organisationId=organisation)
        verification_serializer = OrganisationIdentitySerializer(verification)
        return verification_serializer.data
    except OrganisationIdentity.DoesNotExist:
        return {
            "id": "",
            "organisationId": "",
            "presentationExchangeId": "",
            "presentationState": "",
            "isPresentationVerified": False,
            "presentationRecord": {},
        }


def _get_software_statement_payload(organisation: Organisation) -> dict[str, Any]:
    try:
        software_statement = SoftwareStatement.objects.get(organisationId=organisation)
        return cast(dict[str, Any], software_statement.credentialHistory)
    except SoftwareStatement.DoesNotExist:
        return {}


def _serialize_organisation_summary(organisation: Organisation) -> dict[str, Any]:
    organisation_serializer = OrganisationSerializer(organisation)
    organisation_data = organisation_serializer.data
    organisation_data["softwareStatement"] = _get_software_statement_payload(
        organisation
    )
    return {
        "dataDisclosureAgreements": _build_organisation_ddas(organisation),
        "api": [organisation.openApiUrl],
        "organisation": organisation_data,
        "organisationIdentity": _get_organisation_identity_payload(organisation),
    }


class DataSourceCoverImageView(View):
    def get(
        self, request: HttpRequest, dataSourceId: str, *args: Any, **kwargs: Any
    ) -> HttpResponse | JsonResponse:
        # Get the DataSource instance
        datasource, error_response = get_instance_or_400(
            DataSource, dataSourceId, "Data source not found"
        )
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return get_image_response(datasource.coverImageId, "Cover image not found")


class DataSourceLogoImageView(View):
    def get(
        self, request: HttpRequest, dataSourceId: str, *args: Any, **kwargs: Any
    ) -> HttpResponse | JsonResponse:
        # Get the DataSource instance
        datasource, error_response = get_instance_or_400(
            DataSource, dataSourceId, "Data source not found"
        )
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return get_image_response(datasource.logoId, "Logo image not found")


class DataSourcesView(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        dataSourceId_param = request.GET.get("dataSourceId")

        if dataSourceId_param:
            data_sources_qs: QuerySet[DataSource] = DataSource.objects.filter(
                pk=dataSourceId_param
            )
        else:
            data_sources_qs = DataSource.objects.all().order_by("createdAt")

        data_sources, pagination_data = paginate_queryset(data_sources_qs, request)
        serialized_data_sources = []
        for data_source in data_sources:
            ddas = _build_datasource_ddas(data_source)
            verification_data = _get_datasource_verification_payload(data_source)
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
    def get(
        self, request: HttpRequest, organisationId: str, *args: Any, **kwargs: Any
    ) -> HttpResponse | JsonResponse:
        # Get the organisation instance
        organisation, error_response = get_instance_or_400(
            Organisation, organisationId, "Organisation not found"
        )
        if error_response:
            return error_response

        if organisation is None:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return get_image_response(organisation.coverImageId, "Cover image not found")


class OrganisationLogoImageView(View):
    def get(
        self, request: HttpRequest, organisationId: str, *args: Any, **kwargs: Any
    ) -> HttpResponse | JsonResponse:
        # Get the organisation instance
        organisation, error_response = get_instance_or_400(
            Organisation, organisationId, "Organisation not found"
        )
        if error_response:
            return error_response

        if organisation is None:
            return JsonResponse(
                {"error": "Organisation not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Return the binary image data as the HTTP response
        return get_image_response(organisation.logoId, "Logo image not found")


class OrganisationsView(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        organisation_id_param = request.GET.get("organisationId")
        include_unverified_param = request.GET.get("includeUnverified", "false")

        # Parse includeUnverified parameter
        include_unverified = include_unverified_param.lower() == "true"

        organisations_qs: QuerySet[Organisation]
        if organisation_id_param:
            try:
                organisation_uuid = uuid.UUID(organisation_id_param)
                organisations_qs = Organisation.objects.filter(pk=organisation_uuid)
            except ValueError:
                return JsonResponse({"error": "Invalid organisationId"}, status=400)
            organisations_qs = Organisation.objects.filter(pk=organisation_id_param)
        else:
            organisations_qs = Organisation.objects.all().order_by("createdAt")

        # Filter to only verified organisations unless includeUnverified is true
        if not include_unverified:
            verified_org_ids = OrganisationIdentity.objects.filter(
                isPresentationVerified=True
            ).values_list("organisationId_id", flat=True)
            organisations_qs = organisations_qs.filter(pk__in=verified_org_ids)

        organisations, pagination_data = paginate_queryset(organisations_qs, request)
        serialized_organisations = []
        for organisation in organisations:
            serialized_organisation = _serialize_organisation_summary(organisation)
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
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        search = request.GET.get("search", "")
        search = search.strip()
        if not search:
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
        raw_search_tags = request.GET.get("searchTags")

        def parse_bool_param(
            raw_value: str | None, param_name: str, default: bool = True
        ) -> bool:
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
            search_dataset = parse_bool_param(raw_search_dataset, "searchDataset", True)
            search_tags = parse_bool_param(raw_search_tags, "searchTags", True)
        except ValueError as exc:
            return JsonResponse(
                {
                    "error": "invalid_request",
                    "error_description": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not any(
            [
                search_org_name,
                search_dda_purpose,
                search_dda_description,
                search_dataset,
                search_tags,
            ]
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
            search_dda_purpose
            or search_dda_description
            or search_dataset
            or search_tags
        )

        ddas_qs = DataDisclosureAgreementTemplate.objects.none()
        if dda_scopes_enabled:
            # Use Python filtering for all databases since jsonfield library
            # doesn't support ORM-level nested key lookups
            base_ddas_qs = DataDisclosureAgreementTemplate.objects.filter(
                status="listed",
                isLatestVersion=True,
            ).select_related("organisationId")

            search_lower = search.lower()
            matching_ids = []
            org_ids_set = set()
            for dda in base_ddas_qs:
                record = dda.dataDisclosureAgreementRecord or {}
                purpose = record.get("purpose", "")
                # Check both 'description' and 'purposeDescription' for compatibility
                description = record.get("description", "") or record.get(
                    "purposeDescription", ""
                )

                purpose_matches = search_dda_purpose and search_lower in purpose.lower()
                description_matches = (
                    search_dda_description and search_lower in description.lower()
                )
                tags_matches = (
                    search_tags and search_lower in json.dumps(dda.tags or []).lower()
                )

                if purpose_matches or description_matches or tags_matches:
                    matching_ids.append(dda.id)
                    org_ids_set.add(dda.organisationId.id)

            if matching_ids:
                ddas_qs = base_ddas_qs.filter(id__in=matching_ids)

        org_filter = Q()
        has_filter = False

        if search_org_name:
            org_filter |= (
                Q(name__icontains=search)
                | Q(location__icontains=search)
                | Q(description__icontains=search)
            )
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
            serialized_organisations.append(
                _serialize_organisation_summary(organisation)
            )

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
                    "tags": dda_data.get("tags", []),
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
                "searchTags": search_tags,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            },
        }

        return JsonResponse(response_data)
