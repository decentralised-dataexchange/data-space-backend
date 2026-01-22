from rest_framework import serializers

from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate


class DataDisclosureAgreementsSerializer(
    serializers.ModelSerializer[DataDisclosureAgreement]
):
    class Meta:
        model = DataDisclosureAgreement
        fields = "__all__"


class DataDisclosureAgreementSerializer(
    serializers.ModelSerializer[DataDisclosureAgreement]
):
    class Meta:
        model = DataDisclosureAgreement
        fields = ["dataDisclosureAgreementRecord", "status", "isLatestVersion"]


class DataDisclosureAgreementTemplatesSerializer(
    serializers.ModelSerializer[DataDisclosureAgreementTemplate]
):
    class Meta:
        model = DataDisclosureAgreementTemplate
        fields = "__all__"


class DataDisclosureAgreementTemplateSerializer(
    serializers.ModelSerializer[DataDisclosureAgreementTemplate]
):
    class Meta:
        model = DataDisclosureAgreementTemplate
        fields = [
            "dataDisclosureAgreementRecord",
            "status",
            "isLatestVersion",
            "createdAt",
            "updatedAt",
            "tags",
        ]
