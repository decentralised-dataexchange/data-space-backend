from rest_framework import serializers

from .models import (
    CodeOfConduct,
    Organisation,
    OrganisationIdentity,
    OrganisationIdentityTemplate,
    Sector,
)


class OrganisationSerializer(serializers.ModelSerializer[Organisation]):
    verificationRequestURLPrefix = serializers.CharField(
        source="owsBaseUrl", read_only=True
    )

    class Meta:
        model = Organisation
        fields = [
            "id",
            "coverImageUrl",
            "logoUrl",
            "name",
            "sector",
            "location",
            "policyUrl",
            "description",
            "verificationRequestURLPrefix",
            "openApiUrl",
            "credentialOfferEndpoint",
            "accessPointEndpoint",
            "codeOfConduct",
            "privacyDashboardUrl",
        ]
        read_only_fields = ["id"]


class OrganisationIdentitySerializer(serializers.ModelSerializer[OrganisationIdentity]):
    class Meta:
        model = OrganisationIdentity
        fields = [
            "id",
            "organisationId",
            "presentationExchangeId",
            "presentationState",
            "isPresentationVerified",
            "presentationRecord",
        ]


class OrganisationIdentityTemplateSerializer(
    serializers.ModelSerializer[OrganisationIdentityTemplate]
):
    class Meta:
        model = OrganisationIdentityTemplate
        fields = "__all__"


class SectorSerializer(serializers.ModelSerializer[Sector]):
    class Meta:
        model = Sector
        fields = ["id", "sectorName"]
        read_only_fields = ["id"]


class CodeOfConductSerializer(serializers.ModelSerializer[CodeOfConduct]):
    class Meta:
        model = CodeOfConduct
        fields = ["id", "pdfFileName", "isActive", "createdAt", "updatedAt"]
        read_only_fields = ["id", "pdfFileName", "createdAt", "updatedAt"]
