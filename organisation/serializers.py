from rest_framework import serializers
from .models import (
    Organisation,
    OrganisationIdentity,
    OrganisationIdentityTemplate,
    Sector,
    CodeOfConduct,
)


class OrganisationSerializer(serializers.ModelSerializer):
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


class OrganisationIdentitySerializer(serializers.ModelSerializer):
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


class OrganisationIdentityTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationIdentityTemplate
        fields = "__all__"


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "sectorName"]
        read_only_fields = ["id"]


class CodeOfConductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeOfConduct
        fields = ["id", "pdfFile", "createdAt", "updatedAt"]
        read_only_fields = ["id", "createdAt", "updatedAt"]
