from rest_framework import serializers

from b2b_connection.models import B2BConnection


class B2BConnectionsSerializer(serializers.ModelSerializer[B2BConnection]):
    class Meta:
        model = B2BConnection
        fields = "__all__"


class B2BConnectionSerializer(serializers.ModelSerializer[B2BConnection]):
    class Meta:
        model = B2BConnection
        fields = "__all__"
