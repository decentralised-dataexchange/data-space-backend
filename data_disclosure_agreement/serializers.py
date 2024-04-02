from rest_framework import serializers
import json
from .models import DataDisclosureAgreement

class DataDisclosureAgreementsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataDisclosureAgreement
        fields = '__all__'

class DataDisclosureAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreement
        exclude = ('revisions','dataSourceId')

    def to_representation(self, instance):
        version = self.context['request'].query_params.get('version')
        if version:
            # Check if the specified version matches the main agreement version
            if instance.version == version:
                return super().to_representation(instance)

            # If not found, check in the revisions array for the specified version
            for revision in instance.revisions:
                if revision['version'] == version:
                    # Create a copy of the revision to modify the 'id' field
                    revision_copy = revision.copy()
                    revision_copy['id'] = instance.id  # Obtain the id from the main agreement
                    return revision_copy

            return {}
        else:
            return super().to_representation(instance)
