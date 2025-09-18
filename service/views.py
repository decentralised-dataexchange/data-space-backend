import uuid
import requests
from django.shortcuts import render
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

            organisation_serializer = OrganisationSerializer(organisation)

            api = [organisation.openApiUrl]
            serialized_organisation = {
                "dataDisclosureAgreements": ddas,
                "api": api,
                "organisation": organisation_serializer.data,
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
