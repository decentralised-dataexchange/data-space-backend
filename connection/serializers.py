from rest_framework import serializers

from .models import Connection


class DISPConnectionSerializer(serializers.ModelSerializer[Connection]):
    class Meta:
        model = Connection
        fields = [
            "id",
            "connectionId",
            "connectionState",
            "dataSourceId",
            "connectionRecord",
        ]
