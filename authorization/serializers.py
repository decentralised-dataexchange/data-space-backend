from rest_framework import serializers


class TokenRequestSerializer(serializers.Serializer):
    """Serializer for OAuth 2.0 token request (client_credentials-like)"""

    client_id = serializers.CharField(max_length=255)
    client_secret = serializers.CharField(max_length=255)
    grant_type = serializers.CharField(max_length=50)

    def validate_grant_type(self, value):
        if value != "client_credentials":
            raise serializers.ValidationError(
                "Only 'client_credentials' grant type is supported"
            )
        return value


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for OAuth 2.0 token response"""

    access_token = serializers.CharField()
    token_type = serializers.CharField(default="Bearer")
    expires_in = serializers.IntegerField()
    scope = serializers.CharField(default="", allow_blank=True)
