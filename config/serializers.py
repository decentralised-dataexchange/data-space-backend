from rest_framework import serializers
from .models import DataSource, Verification, VerificationTemplate


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = ['id', 'dataSourceId', 'presentationExchangeId',
                  'presentationState', 'presentationRecord']


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            'id', 'coverImageUrl', 'logoUrl', 'name', 'sector', 'location',
            'policyUrl', 'description', 'openApiUrl'
        ]
        read_only_fields = ['id']


class VerificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationTemplate
        exclude = ['dataSourceId']
