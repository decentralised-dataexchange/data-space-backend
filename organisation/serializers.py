from rest_framework import serializers
from .models import Organisation, OrganisationIdentity, OrganisationIdentityTemplate


class OrganisationSerializer(serializers.ModelSerializer):
    verificationRequestURLPrefix = serializers.CharField(source='owsBaseUrl', read_only=True)
    class Meta:
        model = Organisation
        fields = [
            'id', 'coverImageUrl', 'logoUrl', 'name', 'sector', 'location',
            'policyUrl', 'description', 'verificationRequestURLPrefix', 'openApiUrl'
        ]
        read_only_fields = ['id']

class OrganisationIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationIdentity
        fields = ['id', 'organisationId', 'presentationExchangeId',
                  'presentationState','isPresentationVerified', 'presentationRecord']
        
class OrganisationIdentityTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganisationIdentityTemplate
        fields = "__all__"
