from rest_framework import serializers
from .models import Organisation


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            'id', 'coverImageUrl', 'logoUrl', 'name', 'sector', 'location',
            'policyUrl', 'description', 'owsBaseUrl', 'openApiUrl'
        ]
        read_only_fields = ['id']
