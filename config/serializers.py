from rest_framework import serializers
from .models import DataSource, Verification


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = ['id', 'dataSourceId', 'presentation_exchange_id',
                  'presentation_state', 'presentation_record']


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = [
            'id', 'coverImageUrl', 'logoUrl', 'name', 'sector', 'location',
            'policyUrl', 'description'
        ]
        read_only_fields = ['id']
