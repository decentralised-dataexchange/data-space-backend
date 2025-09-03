from rest_framework import serializers
from .models import OAuth2Clients

class OAuth2ClientsSerializer(serializers.ModelSerializer):
    """Serializer for OAuth2Clients CRUD operations"""
    organisation_name = serializers.CharField(source='organisation.name', read_only=True)
    
    class Meta:
        model = OAuth2Clients
        fields = [
            'id', 'client_id', 'client_secret', 'name', 'description',
            'organisation', 'organisation_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'client_id', 'client_secret', 'created_at', 'updated_at']
        extra_kwargs = {
            'organisation': {'write_only': True}
        }

class OAuth2ClientsCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OAuth2Clients (auto-generates credentials)"""
    
    class Meta:
        model = OAuth2Clients
        fields = ['name', 'description']
    
    def create(self, validated_data):
        # The model's save method will auto-generate client_id and client_secret
        return OAuth2Clients.objects.create(**validated_data)

class OAuth2ClientsUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating OAuth2Clients (excludes credentials)"""
    
    class Meta:
        model = OAuth2Clients
        fields = ['name', 'description', 'is_active']
