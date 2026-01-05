from rest_framework import serializers

from data_disclosure_agreement_record.models import (
    DataDisclosureAgreementRecord,
    DataDisclosureAgreementRecordHistory,
)


class DataDisclosureAgreementRecordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreementRecord
        fields = "__all__"


class DataDisclosureAgreementRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreementRecord
        fields = "__all__"


class DataDisclosureAgreementRecordHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreementRecordHistory
        fields = "__all__"
