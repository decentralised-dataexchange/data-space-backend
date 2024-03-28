from rest_framework import serializers
from .models import Connection


class DISPConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = [
            'id', 'connectionId', 'state', 'myDid', 'theirLabel', 'routingState', 'invitationKey', 'invitationMode', 'initiator', 'updatedAt', 'accept', 'requestId', 'createdAt', 'alias', 'errorMsg', 'inboundConnectionId', 'theirDid', 'theirRole', 'dataSourceId'
        ]
        extra_kwargs = {
            'dataSourceId': {'required': False},
        }
